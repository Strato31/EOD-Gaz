#packages
using JuMP
#use the solver you want
using HiGHS
#package to read excel files
using XLSX
using Dates


#Tmax = 168 #optimization for 1 week (7*24=168 hours)
#Tmax = 61320 #optimization for 1 year (7*24*52 = 61 320 hours)
T_1week = 168 #hours
Nb_weeks = 10
Tmax = 168
indisp_th = 0.1

date_start = DateTime(2023, 1, 1, 0, 0, 0)  # exemple
dates = date_start .+ Hour.(0:Tmax-1)

#data for load and fatal generation
data_file = "Donnees_elec_gaz.xlsx"
#data for load and fatal generation
load = XLSX.readdata(data_file, "Conso_elec", "C3:C8762")
wind = XLSX.readdata(data_file, "Conso_elec", "D3:D8762")
solar = XLSX.readdata(data_file, "Conso_elec", "E3:E8762")
hydro_fatal = XLSX.readdata(data_file, "Conso_elec", "F3:F8762")
thermal_fatal = XLSX.readdata(data_file, "Conso_elec", "G3:G8762")
#total of RES
Pres = wind + solar + hydro_fatal + thermal_fatal

#data for thermal clusters
Nth = 22 #number of thermal generation units, the 10th first are gaz
names = XLSX.readdata(data_file, "Parc_elec", "A2:A23")
dict_th = Dict(i=> names[i] for i in 1:Nth)
costs_th = XLSX.readdata(data_file, "Parc_elec", "H2:H23")
Pmin_th = XLSX.readdata(data_file, "Parc_elec", "F2:F23") #MW
Pmax_th = (1-indisp_th)*XLSX.readdata(data_file, "Parc_elec", "E2:E23") #MW
dmin = XLSX.readdata(data_file, "Parc_elec", "G2:G23") #hours
pos_th_gaz = XLSX.readdata(data_file, "Parc_elec", "L2:L11") # N ou S


#data for hydro reservoir
Nhy = 1 #number of hydro generation units
Pmin_hy = zeros(Nhy)
Pmax_hy = XLSX.readdata(data_file, "Conso_elec", "R2") *ones(Nhy) #MW
e_hy = XLSX.readdata(data_file, "Conso_elec", "S2")*ones(Nhy) #MWh
costs_hy = XLSX.readdata(data_file, "Conso_elec", "Q2")*ones(Nhy) #€/MWh

#costs
cth = repeat(costs_th', Tmax) #cost of thermal generation €/MWh
chy = repeat(costs_hy', Tmax) #cost of hydro generation €/MWh
cuns = 5000*ones(Tmax) #cost of unsupplied energy €/MWh
cexc = 0*ones(Tmax) #cost of in excess energy €/MWh

#data from gaz network
conso_CH4 = XLSX.readdata(data_file, "Conso_gaz", "F2:F8761")
conso_H2 = XLSX.readdata(data_file, "Conso_gaz", "G2:G8761")

# Rendement couplage gaz-élec
r = Dict("CCG" => 0.6, "TAC" => 0.4, "Cogénération" => 0.5)

# Découplage Nord-Sud
ratio_N = XLSX.readdata(data_file, "Données_gaz", "F2")
ratio_S = XLSX.readdata(data_file, "Données_gaz", "F4")
conso_gaz_N = conso_gaz * ratio_nord
conso_gaz_S = conso_gaz * ratio_sud

conso_max_S = (XLSX.readdata(data_file, "Données_gaz", "F5") * 10^3) / 24
conso_max_N = (XLSX.readdata(data_file, "Données_gaz", "F3") * 10^3) / 24

# Stockage
stock_inj_max = XLSX.readdata(data_file, "Données_gaz", "L4") / 24
stock_sout_max = XLSX.readdata(data_file, "Données_gaz", "M4") / 24
stock_max = XLSX.readdata(data_file, "Données_gaz", "K4") * 10^3

## VARIABLES

@variable(model, 0 <= stock_gas[1:Tmax] <= stock_max)
@variable(model, P_import[1:Tmax] >= 0)
@variable(model, P_inj[1:Tmax] >= 0)
@variable(model, P_sout[1:Tmax] >= 0)          
@variable(model, stock[1:Tmax] >= 0)

#data for STEP/battery
#weekly STEP
Pmax_STEP = XLSX.readdata(data_file, "Conso_elec", "R3") #MW
rSTEP = XLSX.readdata(data_file, "Conso_elec", "T3")

#battery
Pmax_battery = 0 #MW
rbattery = 0.85
d_battery = 2 #hours


#############################
#create the optimization model
#############################
model = Model(HiGHS.Optimizer)

#############################
#define the variables
#############################
#thermal generation variables
@variable(model, Pth[1:Tmax,1:Nth] >= 0)
@variable(model, UCth[1:Tmax,1:Nth], Bin)
@variable(model, UPth[1:Tmax,1:Nth], Bin)
@variable(model, DOth[1:Tmax,1:Nth], Bin)
#hydro generation variables
@variable(model, Phy[1:Tmax,1:Nhy] >= 0)
#unsupplied energy variables
@variable(model, Puns[1:Tmax] >= 0)
#in excess energy variables
@variable(model, Pexc[1:Tmax] >= 0)
#weekly STEP variables
@variable(model, Pcharge_STEP[1:Tmax] >= 0)
@variable(model, Pdecharge_STEP[1:Tmax] >= 0)
@variable(model, stock_STEP[1:Tmax] >= 0)
# #battery variables
@variable(model, Pcharge_battery[1:Tmax] >= 0)
@variable(model, Pdecharge_battery[1:Tmax] >= 0)
@variable(model, stock_battery[1:Tmax] >= 0)
#
# #############################
#define the objective function
#############################
@objective(model, Min, sum(Pth.*cth)+sum(Phy.*chy)+Puns'cuns+Pexc'cexc)

#############################
#define the constraints
#############################
#balance constraint
@constraint(model, balance[t in 1:Tmax], sum(Pth[t,g] for g in 1:Nth) + sum(Phy[t,h] for h in 1:Nhy) + Pres[t] + Puns[t] - load[t] - Pexc[t] - Pcharge_STEP[t] + Pdecharge_STEP[t] - Pcharge_battery[t] + Pdecharge_battery[t] == 0)
#thermal unit Pmax constraints
@constraint(model, max_th[t in 1:Tmax, g in 1:Nth], Pth[t,g] <= Pmax_th[g]*UCth[t,g])
#thermal unit Pmin constraints
@constraint(model, min_th[t in 1:Tmax, g in 1:Nth], Pmin_th[g]*UCth[t,g] <= Pth[t,g])
#thermal unit Dmin constraints
for g in 1:Nth
        if (dmin[g] > 1)
            @constraint(model, [t in 2:Tmax], UCth[t,g]-UCth[t-1,g]==UPth[t,g]-DOth[t,g],  base_name = "fct_th_$g")
            @constraint(model, [t in 1:Tmax], UPth[t]+DOth[t]<=1,  base_name = "UPDOth_$g")
            @constraint(model, UPth[1,g]==0,  base_name = "iniUPth_$g")
            @constraint(model, DOth[1,g]==0,  base_name = "iniDOth_$g")
            @constraint(model, [t in dmin[g]:Tmax], UCth[t,g] >= sum(UPth[i,g] for i in (t-dmin[g]+1):t),  base_name = "dminUPth_$g")
            @constraint(model, [t in dmin[g]:Tmax], UCth[t,g] <= 1 - sum(DOth[i,g] for i in (t-dmin[g]+1):t),  base_name = "dminDOth_$g")
            @constraint(model, [t in 1:dmin[g]-1], UCth[t,g] >= sum(UPth[i,g] for i in 1:t), base_name = "dminUPth_$(g)_init")
            @constraint(model, [t in 1:dmin[g]-1], UCth[t,g] <= 1-sum(DOth[i,g] for i in 1:t), base_name = "dminDOth_$(g)_init")
    end
end

#hydro unit constraints
@constraint(model, bounds_hy[t in 1:Tmax, h in 1:Nhy], Pmin_hy[h] <= Phy[t,h] <= Pmax_hy[h])
#hydro stock constraint
@constraint(model, stock_hy[h in 1:Nhy], sum(Phy[t,h] for t in 1:Tmax) <= e_hy[h])

#weekly STEP
@constraint(model, Pcharge_max_STEP[t in 1:Tmax], Pcharge_STEP[t] <= Pmax_STEP)
@constraint(model, Pdecharge_max_STEP[t in 1:Tmax], Pdecharge_STEP[t] <= Pmax_STEP)
@constraint(model, init_stock_STEP, stock_STEP[1] == 0)
@constraint(model, end_Pdecharge_STEP, Pdecharge_STEP[Tmax] <= stock_STEP[Tmax])
@constraint(model, Tmax_stock_STEP, stock_STEP[Tmax] == stock_STEP[1])
@constraint(model, init_Pdecharge_STEP, Pdecharge_STEP[1] == 0)
@constraint(model, evol_stock_STEP[t in 1:Tmax-1], stock_STEP[t+1]-stock_STEP[t]- rSTEP*Pcharge_STEP[t]+Pdecharge_STEP[t]== 0)
@constraint(model, stock_max_STEP[t in 1:Tmax], stock_STEP[t] <= 24*7*Pmax_STEP)

# #battery
@constraint(model, Pcharge_max_battery[t in 1:Tmax], Pcharge_battery[t] <= Pmax_battery)
@constraint(model, Pdecharge_max_battery[t in 1:Tmax], Pdecharge_battery[t] <= Pmax_battery)
@constraint(model, init_stock_battery, stock_battery[1] == 0)
@constraint(model, end_Pdecharge_battery, Pdecharge_battery[Tmax] <= stock_battery[Tmax])
@constraint(model, Tmax_stock_battery, stock_battery[Tmax] == stock_battery[1])
@constraint(model, init_Pdecharge_battery, Pdecharge_battery[1] == 0)
@constraint(model, evol_stock_battery[t in 1:Tmax-1], stock_battery[t+1]-stock_battery[t]- rbattery*Pcharge_battery[t]+1/rbattery*Pdecharge_battery[t]== 0)
@constraint(model, stock_max_battery[t in 1:Tmax], stock_battery[t] <= d_battery*Pmax_battery)




#TODO: solve and analyse the results
#solve the model
optimize!(model)
#------------------------------
#Results
@show termination_status(model)
@show objective_value(model)


#exports results as csv file
th_gen = value.(Pth)
hy_gen = value.(Phy)
STEP_charge = value.(Pcharge_STEP)
STEP_decharge = value.(Pdecharge_STEP)
battery_charge = value.(Pcharge_battery)
battery_decharge = value.(Pdecharge_battery)


# new file created
touch("results.csv")

# file handling in write mode
f = open("results.csv", "w")

write(f, "Date ; ")
for name in names
    write(f, "$name ;")
end
write(f, "Hydro ; STEP pompage ; STEP turbinage ; Batterie injection ; Batterie soutirage ; RES ; load ; Net load \n")

for t in 1:Tmax
    write(f, "$(dates[t]) ; ")

    for g in 1:Nth
        write(f, "$(th_gen[t,g]) ; ")
    end
    for h in 1:Nhy
        write(f, "$(hy_gen[t,h]) ;")
    end
    write(f, "$(STEP_charge[t]) ; $(STEP_decharge[t]) ;")
    write(f, "$(battery_charge[t]) ; $(battery_decharge[t]) ;")
    write(f, "$(Pres[t]) ;  $(load[t]) ; $(load[t]-Pres[t]) \n")

end

close(f)
