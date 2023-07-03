import scanplot

help(scanplot.read_namelists)

data_vars, data_conf = scanplot.read_namelists('/scripts/ensemble/SCANTEC.TESTS')

data_conf

data_vars

help(scanplot.get_dataframe)

dataInicial = data_conf['Starting Time']
dataFinal = data_conf['Ending Time']
Vars = list(map(data_vars.get,[11,12,13])) # ou [*map(data_vars.get,[12,14])]
Stats = ['ACOR', 'RMSE', 'VIES']
Exps = list(data_conf['Experiments'].keys()) # ou [*data_conf["Experiments"].keys()]
outDir = data_conf['Output directory']
figDir = outDir + '/figs'

dTable = scanplot.get_dataframe(dataInicial,dataFinal,Stats,Exps,outDir,series=False)

dTable

dTable['ACORX126_20200601002020081500T.scan']

dTable['ACORX126_20200601002020081500T.scan'].loc[:,'temp:850']

dTable['ACORX126_20200601002020081500T.scan'].loc[:,['temp:850']].plot();

dTable['ACORX126_20200601002020081500T.scan'].loc[:,['temp:850', 'temp:500', 'temp:250']].plot();

axes = dTable['ACORX126_20200601002020081500T.scan'].iloc[:,2:5].plot()

dTable['ACORX126_20200601002020081500T.scan'].loc[:,['temp:850', 'temp:500', 'temp:250']].plot(subplots=True);

axes = dTable['ACORX126_20200601002020081500T.scan'].iloc[:,2:5].plot(subplots=True)

axes = dTable['ACORX126_20200601002020081500T.scan'].iloc[:,1:-1].plot.line(subplots=True, figsize=(15,10), layout=(4,4), sharex=True)

df_exp1 = dTable['ACORX126_20200601002020081500T.scan'].loc[:,['temp:850']]
df_exp2 = dTable['ACORT126_20200601002020081500T.scan'].loc[:,['temp:850']]
ax = df_exp1.plot(label=['exp1', 'exp2'])
df_exp2.plot(ax=ax);

help(scanplot.plot_lines)

scanplot.plot_lines(dTable,Vars,Stats,outDir,figDir=figDir,showFig=True,saveFig=True,combine=False)

scanplot.plot_lines(dTable,Vars,Stats,outDir,figDir=figDir,showFig=True,saveFig=True,combine=True)

lineStyles = ['k--', 'r-', 'g-', 'b-']
scanplot.plot_lines(dTable,Vars,Stats,outDir,figDir=figDir,lineStyles=lineStyles,showFig=True,saveFig=True,combine=True)

help(scanplot.plot_scorecard)

Vars = list(map(data_vars.get,[*data_vars.keys()]))

scanplot.plot_scorecard(dTable,Vars,Stats,'ganho',Exps,outDir,figDir=figDir,showFig=True,saveFig=True)

Exps = ['T126', 'TENM']
scanplot.plot_scorecard(dTable,Vars,Stats,'ganho',Exps,outDir,figDir=figDir,showFig=True,saveFig=True)

scanplot.plot_scorecard(dTable,Vars,Stats,'fc',Exps,outDir,figDir=figDir,showFig=True,saveFig=True)

help(scanplot.plot_dTaylor)

Vars = list(map(data_vars.get,[12,13]))

scanplot.plot_dTaylor(dTable,data_conf,Vars,Stats,outDir,figDir=figDir,showFig=True,saveFig=True)

help(scanplot.plot_lines_tStudent)

Exps = list(data_conf['Experiments'].keys())

dTable_series = scanplot.get_dataframe(dataInicial,dataFinal,Stats,Exps,outDir,series=True)

dTable_series

Var = Vars[0][0].lower()

VarName = Vars[0][1]

varlev_exps = scanplot.concat_tables_and_loc(dTable,dataInicial,dataFinal,Exps,Var,series=False)

varlev_dia_exps = scanplot.concat_tables_and_loc(dTable_series,dataInicial,dataFinal,Exps,Var,series=True)

lst_varlev_dia_exps_rsp = scanplot.df_fill_nan(varlev_exps,varlev_dia_exps)

ldrom_exp, ldrosup_exp, ldroinf_exp = scanplot.calc_tStudent(lst_varlev_dia_exps_rsp)

scanplot.plot_lines_tStudent(dataInicial,dataFinal,dTable_series,Exps,Var,VarName,ldrom_exp,ldrosup_exp,ldroinf_exp,varlev_exps,outDir,figDir=figDir,saveFig=True,showFig=True)

lineStyles = ['b', 'g', 'r', 'k']
scanplot.plot_lines_tStudent(dataInicial,dataFinal,dTable_series,Exps,Var,VarName,ldrom_exp,ldrosup_exp,ldroinf_exp,varlev_exps,outDir,figDir=figDir,lineStyles=lineStyles,saveFig=True,showFig=True)
