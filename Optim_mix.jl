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
pos_th_gaz = XLSX.readdata(data_file, "Parc_elec", "L2:L11") # N ou S, les 6 premières au sud, et les 4 suivantes au nord


#data for hydro reservoir
Nhy = 1 #number of hydro generation units
Pmin_hy = zeros(Nhy)
Pmax_hy = XLSX.readdata(data_file, "Conso_elec", "R2") *ones(Nhy) #MW
e_hy = XLSX.readdata(data_file, "Conso_elec", "S2")*ones(Nhy) #MWh
costs_hy = XLSX.readdata(data_file, "Conso_elec", "Q2")*ones(Nhy) #€/MWh

#costs elec
cth = repeat(costs_th', Tmax) #cost of thermal generation €/MWh
chy = repeat(costs_hy', Tmax) #cost of hydro generation €/MWh
cuns_elec = 5000*ones(Tmax) #cost of unsupplied energy €/MWh
cexc_elec = 0*ones(Tmax) #cost of in excess energy €/MWh

#data from gaz network
conso_CH4 = XLSX.readdata(data_file, "Conso_gaz", "F2:F8761")* 10^3
conso_H2_N = XLSX.readdata(data_file, "Conso_gaz", "G2:G8761")* 10^3 # pas de conso au Sud



# Rendement couplage gaz-élec
r = Dict("CCG" => 0.6, "TAC" => 0.4, "Cogénération" => 0.5, "Electrolyse" => 0.7, "Vaporeformage"=> 0.7)

# Découplage Nord-Sud
ratio_N = XLSX.readdata(data_file, "Données_gaz", "F2")
ratio_S = XLSX.readdata(data_file, "Données_gaz", "F4")
conso_CH4_N = conso_CH4 * ratio_N
conso_CH4_S = conso_CH4 * ratio_S
cap_CH4_S_to_N = XLSX.readdata(data_file, "Données_gaz", "F9")* 10^3/24
cap_H2_S_to_N = XLSX.readdata(data_file, "Données_gaz", "F31")* 10^3/24

# Stockage
cap_CH4_inj_max = XLSX.readdata(data_file, "Données_gaz", "L4") * 10^3/ 24
cap_CH4_sout_max = XLSX.readdata(data_file, "Données_gaz", "M4")* 10^3 / 24
stock_CH4_max_S = XLSX.readdata(data_file, "Données_gaz", "K4") * 10^6 * 0.4
stock_CH4_max_N = XLSX.readdata(data_file, "Données_gaz", "K4")* 10^6 * 0.6 # on stocke là où il y a moins d'import
high_lev_CH4 = XLSX.readdata(data_file, "Conso_gaz", "N2:N8761")
low_lev_CH4 = XLSX.readdata(data_file, "Conso_gaz", "O2:O8761")
c_slack_CH4 = 1e6  # €/MWh (à ajuster selon ton modèle)

# production gaz CH4
N_CH4 = 2 # 2 moyens de production de gaz au sud et 2 au nord
Pmax_CH4_S = XLSX.readdata(data_file, "Données_gaz", "H14:H15") * 10^3/ 24
Pmax_CH4_N = XLSX.readdata(data_file, "Données_gaz", "H16:H17") * 10^3/ 24
Pmin_CH4_S = XLSX.readdata(data_file, "Données_gaz", "I14:I15") * 10^3/ 24
Pmin_CH4_N = XLSX.readdata(data_file, "Données_gaz", "I16:I17") * 10^3/ 24
dmin_CH4_S = XLSX.readdata(data_file, "Données_gaz", "J14:J15")
dmin_CH4_N = XLSX.readdata(data_file, "Données_gaz", "J16:J17")
costs_CH4_S = XLSX.readdata(data_file, "Données_gaz", "K14:K15")
costs_CH4_N = XLSX.readdata(data_file, "Données_gaz", "K16:K17")


# production H2
N_H2 = 1
Pmax_H2_S = XLSX.readdata(data_file, "Données_gaz", "H36") * 10^3/ 24
Pmax_H2_N = XLSX.readdata(data_file, "Données_gaz", "H37") * 10^3/ 24
Pmin_H2_S = XLSX.readdata(data_file, "Données_gaz", "I36") * 10^3/ 24
Pmin_H2_N = XLSX.readdata(data_file, "Données_gaz", "I37") * 10^3/ 24
dmin_H2_S = XLSX.readdata(data_file, "Données_gaz", "J36")
dmin_H2_N = XLSX.readdata(data_file, "Données_gaz", "J37")
costs_H2_S = XLSX.readdata(data_file, "Données_gaz", "K36")
costs_H2_N = XLSX.readdata(data_file, "Données_gaz", "K37")

#costs gaz
c_CH4_S = repeat(costs_CH4_S', Tmax) 
c_CH4_N = repeat(costs_CH4_N', Tmax) 
c_H2_S = fill(costs_H2_S, Tmax, 1)
c_H2_N = fill(costs_H2_N, Tmax, 1)
cuns_gaz = 500*ones(Tmax) # cost of unsupplied gaz €/MWh, facteur 10, dépend du secteur , Value of Lost Load 


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
@variable(model, Puns_elec[1:Tmax] >= 0)
#in excess energy variables
@variable(model, Pexc_elec[1:Tmax] >= 0)

#CH4 variables
@variable(model, P_CH4_S[1:Tmax,1:N_CH4] >= 0)
@variable(model, P_CH4_N[1:Tmax,1:N_CH4] >= 0)
@variable(model, UC_CH4_S[1:Tmax,1:N_CH4], Bin)
@variable(model, UC_CH4_N[1:Tmax,1:N_CH4] , Bin)
@variable(model, UP_CH4_S[1:Tmax,1:N_CH4] , Bin)
@variable(model, UP_CH4_N[1:Tmax,1:N_CH4] , Bin)
@variable(model, DO_CH4_S[1:Tmax,1:N_CH4], Bin)
@variable(model, DO_CH4_N[1:Tmax,1:N_CH4] , Bin)
@variable(model, flux_CH4_S_to_N[1:Tmax] )
@variable(model, Puns_CH4_S[1:Tmax,1:N_CH4] >= 0)
@variable(model, Puns_CH4_N[1:Tmax,1:N_CH4] >= 0)

@variable(model, stock_CH4_S[1:Tmax] >= 0)
@variable(model, stock_CH4_N[1:Tmax] >= 0)
@variable(model, P_inj_CH4_S[1:Tmax] >= 0)
@variable(model, P_inj_CH4_N[1:Tmax] >= 0)
@variable(model, P_sout_CH4_S[1:Tmax] >= 0)
@variable(model, P_sout_CH4_N[1:Tmax] >= 0)
@variable(model, slack_CH4_S_low[1:Tmax] >= 0)
@variable(model, slack_CH4_S_high[1:Tmax] >= 0)
@variable(model, slack_CH4_N_low[1:Tmax] >= 0)
@variable(model, slack_CH4_N_high[1:Tmax] >= 0)


#H2 variables
@variable(model, P_H2_S[1:Tmax] >= 0)
@variable(model, P_H2_N[1:Tmax] >= 0)
@variable(model, UC_H2_S[1:Tmax] , Bin)
@variable(model, UC_H2_N[1:Tmax] , Bin)
@variable(model, UP_H2_S[1:Tmax] , Bin)
@variable(model, UP_H2_N[1:Tmax] , Bin)
@variable(model, DO_H2_S[1:Tmax] , Bin)
@variable(model, DO_H2_N[1:Tmax], Bin)
@variable(model, flux_H2_S_to_N[1:Tmax] )
@variable(model, Puns_H2_S[1:Tmax] >= 0)
@variable(model, Puns_H2_N[1:Tmax] >= 0)

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
@objective(model, Min,
    sum(Pth[t,g] * cth[t,g] for t in 1:Tmax, g in 1:Nth)
  + sum(Phy[t,h] * chy[t,h] for t in 1:Tmax, h in 1:Nhy)
  + sum(P_CH4_S[t,g] * c_CH4_S[t,g] for t in 1:Tmax, g in 1:N_CH4)
  + sum(P_CH4_N[t,g] * c_CH4_N[t,g] for t in 1:Tmax, g in 1:N_CH4)
  + sum(P_H2_S[t] * c_H2_S[t,1] for t in 1:Tmax)
  + sum(P_H2_N[t] * c_H2_N[t,1] for t in 1:Tmax)
  + sum(Puns_elec[t] * cuns_elec[t] for t in 1:Tmax)
  + sum(Pexc_elec[t] * cexc_elec[t] for t in 1:Tmax)
  + sum(Puns_CH4_S[t,g] * cuns_gaz[t] for t in 1:Tmax, g in 1:N_CH4)
  + sum(Puns_CH4_N[t,g] * cuns_gaz[t] for t in 1:Tmax, g in 1:N_CH4)
  + sum(Puns_H2_S[t] * cuns_gaz[t] for t in 1:Tmax)
  + sum(Puns_H2_N[t] * cuns_gaz[t] for t in 1:Tmax)
  + c_slack_CH4 * ( sum(slack_CH4_S_low[t] + slack_CH4_S_high[t] for t in 1:Tmax) + sum(slack_CH4_N_low[t] + slack_CH4_N_high[t] for t in 1:Tmax) )
)


#############################
#define the constraints
#############################
#balance constraint for elec
@constraint(model, balance_elec[t in 1:Tmax], sum(Pth[t,g] for g in 1:Nth) + sum(Phy[t,h] for h in 1:Nhy) + Pres[t] + Puns_elec[t] - load[t] - Pexc_elec[t] - Pcharge_STEP[t] + Pdecharge_STEP[t] - Pcharge_battery[t] + Pdecharge_battery[t] - P_H2_S[t]/r["Electrolyse"] == 0)
#balance constraint for gas
@constraint(model, balance_CH4_S[t in 1:Tmax], sum(P_CH4_S[t,g] for g in 1:N_CH4) + P_sout_CH4_S[t] - P_inj_CH4_S[t] - conso_CH4_S[t] - flux_CH4_S_to_N[t] - sum(Pth[t,g] for g in 1:3)/r["CCG"] - sum(Pth[t,g] for g in 4:5)/r["TAC"] - Pth[t,6]/r["Cogénération"] == 0)
@constraint(model, balance_CH4_N[t in 1:Tmax], sum(P_CH4_N[t,g] for g in 1:N_CH4) + P_sout_CH4_N[t] - P_inj_CH4_N[t] - conso_CH4_N[t] + flux_CH4_S_to_N[t] - sum(Pth[t,g] for g in 7:10)/r["CCG"] - P_H2_N[t]/r["Vaporeformage"] == 0)
@constraint(model, balance_H2_S[t in 1:Tmax], P_H2_S[t] - flux_H2_S_to_N[t] ==0)
@constraint(model, balance_H2_N[t in 1:Tmax], P_H2_N[t] + flux_H2_S_to_N[t] - conso_H2_N[t] ==0)
#Pmax constraints
@constraint(model, max_th[t in 1:Tmax, g in 1:Nth], Pth[t,g] <= Pmax_th[g]*UCth[t,g])
@constraint(model, max_CH4_N[t in 1:Tmax, g in 1:N_CH4], P_CH4_N[t,g] <= Pmax_CH4_N[g]*UC_CH4_N[t,g])
@constraint(model, max_CH4_S[t in 1:Tmax, g in 1:N_CH4], P_CH4_S[t,g] <= Pmax_CH4_S[g]*UC_CH4_S[t,g])
@constraint(model, max_H2_N[t in 1:Tmax], P_H2_N[t] <= Pmax_H2_N*UC_H2_N[t])
@constraint(model, max_H2_S[t in 1:Tmax], P_H2_S[t] <= Pmax_H2_S*UC_H2_S[t])
@constraint(model, max_flux_CH4[t in 1:Tmax], flux_CH4_S_to_N[t] <= cap_CH4_S_to_N)
@constraint(model, max_flux_H2[t in 1:Tmax], flux_H2_S_to_N[t] <= cap_H2_S_to_N)

#Pmin constraints
@constraint(model, min_th[t in 1:Tmax, g in 1:Nth], Pmin_th[g]*UCth[t,g] <= Pth[t,g])
@constraint(model, min_CH4_N[t in 1:Tmax, g in 1:N_CH4], Pmin_CH4_N[g]*UC_CH4_N[t,g] <= P_CH4_N[t,g] )
@constraint(model, min_CH4_S[t in 1:Tmax, g in 1:N_CH4], P_CH4_S[t,g] >= Pmin_CH4_S[g]*UC_CH4_S[t,g])
@constraint(model, min_H2_N[t in 1:Tmax], P_H2_N[t] >= Pmin_H2_N*UC_H2_N[t])
@constraint(model, min_H2_S[t in 1:Tmax], P_H2_S[t] >= Pmin_H2_S*UC_H2_S[t])
@constraint(model, min_flux_H2[t in 1:Tmax], flux_H2_S_to_N[t] >= - cap_H2_S_to_N)

#Dmin constraints
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

for g in 1:N_CH4
    if dmin_CH4_S[g] > 1
        @constraint(model, [t in 2:Tmax],UC_CH4_S[t,g] - UC_CH4_S[t-1,g] == UP_CH4_S[t,g] - DO_CH4_S[t,g])
        @constraint(model, [t in 1:Tmax],UP_CH4_S[t,g] + DO_CH4_S[t,g] <= 1)
        @constraint(model, UP_CH4_S[1,g] == 0)
        @constraint(model, DO_CH4_S[1,g] == 0)
        @constraint(model, [t in dmin_CH4_S[g]:Tmax], UC_CH4_S[t,g] >= sum(UP_CH4_S[i,g] for i in t-dmin_CH4_S[g]+1:t))
        @constraint(model, [t in dmin_CH4_S[g]:Tmax], UC_CH4_S[t,g] <= 1 - sum(DO_CH4_S[i,g] for i in t-dmin_CH4_S[g]+1:t))
        @constraint(model, [t in 1:dmin_CH4_S[g]-1], UC_CH4_S[t,g] >= sum(UP_CH4_S[i,g] for i in 1:t))
        @constraint(model, [t in 1:dmin_CH4_S[g]-1], UC_CH4_S[t,g] <= 1 - sum(DO_CH4_S[i,g] for i in 1:t))
    end
end

for g in 1:N_CH4
    if dmin_CH4_N[g] > 1
        @constraint(model, [t in 2:Tmax], UC_CH4_N[t,g] - UC_CH4_N[t-1,g] == UP_CH4_N[t,g] - DO_CH4_N[t,g])
        @constraint(model, [t in 1:Tmax], UP_CH4_N[t,g] + DO_CH4_N[t,g] <= 1)
        @constraint(model, UP_CH4_N[1,g] == 0)
        @constraint(model, DO_CH4_N[1,g] == 0)
        @constraint(model, [t in dmin_CH4_N[g]:Tmax], UC_CH4_N[t,g] >= sum(UP_CH4_N[i,g] for i in t-dmin_CH4_N[g]+1:t))
        @constraint(model, [t in dmin_CH4_N[g]:Tmax], UC_CH4_N[t,g] <= 1 - sum(DO_CH4_N[i,g] for i in t-dmin_CH4_N[g]+1:t))
    end
end

if dmin_H2_S > 1
    @constraint(model, [t in 2:Tmax], UC_H2_S[t] - UC_H2_S[t-1] == UP_H2_S[t] - DO_H2_S[t])
    @constraint(model, [t in 1:Tmax], UP_H2_S[t] + DO_H2_S[t] <= 1)
    @constraint(model, UP_H2_S[1] == 0)
    @constraint(model, DO_H2_S[1] == 0)
    @constraint(model, [t in dmin_H2_S:Tmax], UC_H2_S[t] >= sum(UP_H2_S[i] for i in t-dmin_H2_S+1:t))
    @constraint(model, [t in dmin_H2_S:Tmax], UC_H2_S[t] <= 1 - sum(DO_H2_S[i] for i in t-dmin_H2_S+1:t))
end

if dmin_H2_N > 1
    @constraint(model, [t in 2:Tmax], UC_H2_N[t] - UC_H2_N[t-1] == UP_H2_N[t] - DO_H2_N[t])
    @constraint(model, [t in 1:Tmax], UP_H2_N[t] + DO_H2_N[t] <= 1)
    @constraint(model, UP_H2_N[1] == 0)
    @constraint(model, DO_H2_N[1] == 0)
    @constraint(model, [t in dmin_H2_N:Tmax], UC_H2_N[t] >= sum(UP_H2_N[i] for i in t-dmin_H2_N+1:t))
    @constraint(model, [t in dmin_H2_N:Tmax], UC_H2_N[t] <= 1 - sum(DO_H2_N[i] for i in t-dmin_H2_N+1:t))
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

# battery
@constraint(model, Pcharge_max_battery[t in 1:Tmax], Pcharge_battery[t] <= Pmax_battery)
@constraint(model, Pdecharge_max_battery[t in 1:Tmax], Pdecharge_battery[t] <= Pmax_battery)
@constraint(model, init_stock_battery, stock_battery[1] == 0)
@constraint(model, end_Pdecharge_battery, Pdecharge_battery[Tmax] <= stock_battery[Tmax])
@constraint(model, Tmax_stock_battery, stock_battery[Tmax] == stock_battery[1])
@constraint(model, init_Pdecharge_battery, Pdecharge_battery[1] == 0)
@constraint(model, evol_stock_battery[t in 1:Tmax-1], stock_battery[t+1]-stock_battery[t]- rbattery*Pcharge_battery[t]+1/rbattery*Pdecharge_battery[t]== 0)
@constraint(model, stock_max_battery[t in 1:Tmax], stock_battery[t] <= d_battery*Pmax_battery)

# stockage CH4
# @constraint(model, evol_stock_CH4_S[t in 1:Tmax-1], stock_CH4_S[t+1] - stock_CH4_S[t] - P_inj_CH4_S[t] + P_sout_CH4_S[t] == 0)
# @constraint(model, stock_max_CH4_S[t in 1:Tmax], stock_CH4_S[t] <= stock_CH4_max_S)
# @constraint(model, inj_max_CH4_S[t in 1:Tmax], P_inj_CH4_S[t] <= cap_CH4_inj_max)
# @constraint(model, sout_max_CH4_S[t in 1:Tmax], P_sout_CH4_S[t] <= cap_CH4_sout_max)
@constraint(model, init_stock_CH4_S, stock_CH4_S[1] == 0)
@constraint(model, stock_CH4_S_high[t in 1:Tmax], stock_CH4_S[t] <= high_lev_CH4[t]*stock_CH4_max_S + slack_CH4_S_high[t])
@constraint(model, stock_CH4_S_low[t in 1:Tmax], low_lev_CH4[t]*stock_CH4_max_S - slack_CH4_S_low[t] <= stock_CH4_S[t])

#@constraint(model, end_stock_CH4_S, stock_CH4_S[Tmax] == stock_CH4_S[1])

@constraint(model, evol_stock_CH4_N[t in 1:Tmax-1], stock_CH4_N[t+1] - stock_CH4_N[t] - P_inj_CH4_N[t] + P_sout_CH4_N[t] == 0)
@constraint(model, stock_max_CH4_N[t in 1:Tmax], stock_CH4_N[t] <= stock_CH4_max_N)
@constraint(model, inj_max_CH4_N[t in 1:Tmax], P_inj_CH4_N[t] <= cap_CH4_inj_max)
@constraint(model, sout_max_CH4_N[t in 1:Tmax], P_sout_CH4_N[t] <= cap_CH4_sout_max)
@constraint(model, init_stock_CH4_N, stock_CH4_N[1] == 0)
@constraint(model, stock_CH4_N_high[t in 1:Tmax], stock_CH4_N[t] <= high_lev_CH4[t]*stock_CH4_max_N + slack_CH4_N_high[t])
@constraint(model, stock_CH4_N_low[t in 1:Tmax], low_lev_CH4[t]*stock_CH4_max_N - slack_CH4_N_low[t] <= stock_CH4_N[t])

#@constraint(model, end_stock_CH4_N, stock_CH4_N[Tmax] == stock_CH4_N[1])



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

P_CH4_S_val = value.(P_CH4_S)
P_CH4_N_val = value.(P_CH4_N)
stock_CH4_S_val = value.(stock_CH4_S)
stock_CH4_N_val = value.(stock_CH4_N)
P_inj_CH4_S_val = value.(P_inj_CH4_S)
P_inj_CH4_N_val = value.(P_inj_CH4_N)
P_sout_CH4_S_val = value.(P_sout_CH4_S)
P_sout_CH4_N_val = value.(P_sout_CH4_N)
flux_CH4_val = value.(flux_CH4_S_to_N)

P_H2_S_val = value.(P_H2_S)
P_H2_N_val = value.(P_H2_N)
flux_H2_val = value.(flux_H2_S_to_N)

Puns_CH4_S_val = value.(Puns_CH4_S)
Puns_CH4_N_val = value.(Puns_CH4_N)
Puns_H2_S_val = value.(Puns_H2_S)
Puns_H2_N_val = value.(Puns_H2_N)



# new file created
touch("results.csv")

# file handling in write mode
f = open("results_with_gaz.csv", "w")

write(f, "Date ; ")
for name in names
    write(f, "$name ;")
end
write(f,
"Hydro ; STEP_pompage ; STEP_turbinage ; Batt_inj ; Batt_sout ; RES ; Load ; Net_load ; " *
"CH4_S_prod ; CH4_N_prod ; CH4_S_inj ; CH4_S_sout ; CH4_N_inj ; CH4_N_sout ; " *
"CH4_S_stock ; CH4_N_stock ; CH4_flux_S_N ; " *
"H2_S_prod ; H2_N_prod ; H2_flux_S_N ; " *
"CH4_S_uns ; CH4_N_uns ; H2_S_uns ; H2_N_uns \n"
)

for t in 1:Tmax
    write(f, "$(dates[t]) ; ")

    for g in 1:Nth
        write(f, "$(th_gen[t,g]) ; ")
    end

    for h in 1:Nhy
        write(f, "$(hy_gen[t,h]) ; ")
    end

    write(f,
        "$(STEP_charge[t]) ; $(STEP_decharge[t]) ; " *
        "$(battery_charge[t]) ; $(battery_decharge[t]) ; " *
        "$(Pres[t]) ; $(load[t]) ; $(load[t]-Pres[t]) ; " *
        "$(sum(P_CH4_S_val[t,g] for g in 1:N_CH4)) ; " *
        "$(sum(P_CH4_N_val[t,g] for g in 1:N_CH4)) ; " *
        "$(P_inj_CH4_S_val[t]) ; $(P_sout_CH4_S_val[t]) ; " *
        "$(P_inj_CH4_N_val[t]) ; $(P_sout_CH4_N_val[t]) ; " *
        "$(stock_CH4_S_val[t]) ; $(stock_CH4_N_val[t]) ; " *
        "$(flux_CH4_val[t]) ; " *
        "$(P_H2_S_val[t]) ; $(P_H2_N_val[t]) ; $(flux_H2_val[t]) ; " *
        "$(sum(Puns_CH4_S_val[t,g] for g in 1:N_CH4)) ; " *
        "$(sum(Puns_CH4_N_val[t,g] for g in 1:N_CH4)) ; " *
        "$(Puns_H2_S_val[t]) ; $(Puns_H2_N_val[t]) \n"
    )
end


close(f)
