#! /usr/bin/env python3

# SCANPLOT - Um sistema de plotagem simples para o SCANTEC
# CC-BY-NC-SA-4.0 2022 INPE

import global_variables as gvars

import os
import numpy as np
import pandas as pd

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import rcParams

import cartopy.crs as ccrs
from cartopy.feature import NaturalEarthFeature, LAND, COASTLINE
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

from IPython import get_ipython

import seaborn as sns

import skill_metrics as sm

from scipy.stats import t
from scipy.stats import ttest_ind

from aux_functions import isnotebook

import hvplot.xarray
import holoviews as hv
from holoviews import opts
import panel as pn
import param

# Esta instrução é utilizada em conjunto com a opção showFig
# para determinar se o script está sendo chamado a partir de uma seção
# iterativa ou pelo shell padrão do Python
ipython = get_ipython()

def plot_lines(dTable,Vars,Stats,outDir,**kwargs):

    """
    plot_lines
    ==========
    
    Esta função plota gráficos de linha a partir de um dicionário de dataframes com as tabelas do SCANTEC.
    
    Parâmetros de entrada
    ---------------------
        dTable : objeto dicionário com uma ou mais tabelas do SCANTEC;
        Vars   : lista com os nomes e níveis das variáveis;
        Stats  : lista com os nomes das estatísticas a serem processadas;
        outDir : string com o diretório com as tabelas do SCANTEC.

    Parâmetros de entrada opcionais
    -------------------------------
        showFig    : valor Booleano para mostrar ou não as figuras durante a plotagem
                     showFig=False (valor padrão), não mostra as figuras (mais rápido)
                     showFig=True, mostra as figuras (mais lento);
        saveFig    : valor Booleano para salvar ou não as figuras durante a plotagem:
                     * saveFig=False (valor padrão), não salva as figuras;
                     * saveFig=True, salva as figuras;
        lineStyles : lista com as cores e os estilos das linhas (o número de elementos
                     da lista deve ser igual ao número de experimentos);
        figDir     : string com o diretório onde as figuras serão salvas;
        combine    : valor Booleano para combinar as curvas dos experimentos em um só gráfico:
                     * combine=False (valor padrão), plota as curvas em gráficos separados;
                     * combine=True, plota as curvas das mesmas estatísticas no mesmo gráfico;
        tExt       : string com o extensão dos nomes das tabelas do SCANTEC:
                     * tExt='scan' (valor padrão), considera as tabelas do SCANTEC;
                     * tExt='scam', considera os nomes das tabelas das versões antigas do SCANTEC.
   
    Resultado
    ---------
        Figuras salvas no diretório definido na variável outDir ou figDir. Se figDir não
        for passado, então as figuras são salvas no diretório outDir (SCANTEC/dataout).
    
    Uso
    ---
        import scanplot 
        
        data_vars, data_conf = scanplot.read_namelists("~/SCANTEC")
        
        dataInicial = data_conf["Starting Time"]
        dataFinal = data_conf["Ending Time"]
        Vars = list(map(data_vars.get,[*data_vars.keys()]))
        Stats = ["ACOR", "RMSE", "VIES"]
        Exps = list(data_conf["Experiments"].keys())
        outDir = data_conf["Output directory"]
       
        figDir = data_conf["Output directory"]
 
        lineStyles = ['k-', 'b-', 'b--', 'r-', 'r--']

        dTable = scanplot.get_dataframe(dataInicial,dataFinal,Stats,Exps,outDir)
        
        scanplot.plot_lines(dTable,Vars,Stats,outDir,showFig=True,saveFig=True,lineStyles=lineStyles,figDir=figDir)
    """
  
    # tExt é uma variável global e o seu valor é sempre atualizado
    global tExt

    # Verifica se foram passados os argumentos opcionais e atribui os valores
    if 'combine' in kwargs:
        combine = kwargs['combine']
    else:
        combine = gvars.combine

    if 'tExt' in kwargs:
        tExt = kwargs['tExt']      
        # Atualiza o valor global de tExt
        gvars.tExt = tExt
    else:
        tExt = gvars.tExt

    if 'figDir' in kwargs:
        figDir = kwargs['figDir']
        # Verifica se o diretório figDir existe e cria se necessário
        if not os.path.exists(figDir):
            os.makedirs(figDir)
    else:
        figDir = outDir

    if 'showFig' in kwargs:
        showFig = kwargs['showFig']
    else:
        showFig = gvars.showFig

    if 'saveFig' in kwargs:
        saveFig = kwargs['saveFig']
    else:
        saveFig = gvars.saveFig

    if 'lineStyles' in kwargs:
        lineStyles = kwargs['lineStyles']
    else:
        lineStyles = gvars.lineStyles

    # Define o backend de plotagem do matplotlib
    # Agg: não mostra os gráficos
    # inline: mostra os gráficos
    # Refs:
    # * https://stackoverflow.com/questions/43545050/using-matplotlib-notebook-after-matplotlib-inline-in-jupyter-notebook-doesnt
    # * https://www.codegrepper.com/code-examples/python/use+ipython+magic+in+script
    ipython.magic("matplotlib Agg")           
    ipython.magic("matplotlib Agg")           
    import matplotlib.pyplot as plt

    # Reseta os parâmetros de aspecto do Seaborn
    sns.reset_orig()

    # Opção combine=True    
    if combine:
    
        if isnotebook(get_ipython().__class__.__name__): # seções iterativas
            if showFig:
                ipython.magic('matplotlib inline')           
                #mpl.rc('figure', max_open_warning = 0)
                mpl.rcParams.update({'figure.max_open_warning': 0})
            else:
                ipython.magic('matplotlib agg')           
        else: # seções não iterativas
            if not showFig:
                mpl.use('agg')
                mpl.rcParams.update({'figure.max_open_warning': 0})

        for var in range(len(Vars)):
       
            for Stat in Stats:
                # Nomes das tabelas
                Tables = list(filter(lambda x:Stat in x, [*dTable.keys()]))
       
                # Lista de tabelas a serem plotadas
                dfTables = []
    
                for table in Tables:
                    if tExt == 'scan':
                        df_exp = dTable[table].loc[:,[Vars[var][0].lower()]]
                    else:
                        df_exp = dTable[table].loc[:,[Vars[var][0]]]
                    dfTables.append(df_exp)
        
                fcts = dTable[table].loc[:,"%Previsao"].values

                # Cria o objeto com o gráfico principal
                # Se lineStyles=True
                if lineStyles:
                    ax = pd.concat(dfTables,axis=1).plot(title=Vars[var][1],
                                                         figsize=(8,5),
                                                         fontsize=12,
                                                         linewidth=1.5,
                                                         style=lineStyles)
                # Se lineStyles=False (padrão)
                else:
                    ax = pd.concat(dfTables,axis=1).plot(title=Vars[var][1],
                                                         figsize=(8,5),
                                                         fontsize=12,
                                                         linewidth=1.5,
                                                         marker='o')

                ax.set_xticks(dTable[table].index)
                ax.set_xticklabels(fcts)

                # Legendas
                enames=[]
                for table in Tables:
                    enames.append(table.split('_')[0][4:])
                    
                ax.legend(enames)
                
                plt.ylabel(Stat)
                plt.xlabel('Horas de Integração')
                plt.xticks(rotation=90)

                # Plota y=0.5 para ACOR e y=0.0 para demais tabelas
                if Stat == 'ACOR':
                    plt.axhline(y=0.5, color='black', linestyle='-', linewidth=1)
                else:
                    plt.axhline(y=0.0, color='black', linestyle='-', linewidth=1)
  
                # Grade do gráfico
                plt.grid(color='grey', linestyle='--', linewidth=0.5)
               
                # Se saveFig=True
                if saveFig: 
                    #fig_name = table.replace(str(tExt),'') + Vars[var][0] + '-combined.png'
                    if tExt == 'scan':
                        fig_name = table.replace(table[4:table.find('_')],'EXPS').replace('T.'+str(tExt),'') + Vars[var][0].replace(':','') + '-combined.png'
                    else:
                        fig_name = table.replace(table[4:table.find('_')],'EXPS').replace('T.'+str(tExt),'') + Vars[var][0].replace('-','') + '-combined.png'
                    plt.savefig(os.path.join(figDir, fig_name), bbox_inches='tight', dpi=120)

        if showFig:
            plt.show()

        plt.close()

    # Opção combine=False (padrão)
    else:
            
        if isnotebook(get_ipython().__class__.__name__):
            if showFig:
                ipython.magic('matplotlib inline')           
                mpl.rcParams.update({'figure.max_open_warning': 0})
            else:
                ipython.magic('matplotlib agg')           
        else:
            if not showFig:
                mpl.use('agg')
                mpl.rcParams.update({'figure.max_open_warning': 0})

        for table in list(dTable.keys()):
            Stat = table[0:4]
            fcts = dTable[table].loc[:,"%Previsao"].values

            fig, ax = plt.subplots()
            plt.rcParams.update({'figure.max_open_warning': 0})

            for var in range(len(Vars)):
                vname = Vars[var]

                if tExt == 'scan':            
                    ax = dTable[table].loc[:,[Vars[var][0].lower()]].plot(title=Vars[var][1], 
                                                                          figsize=(8,5),
                                                                          fontsize=12,
                                                                          linewidth=1.5,
                                                                          marker='o')
                else:
                    ax = dTable[table].loc[:,[Vars[var][0]]].plot(title=Vars[var][1], 
                                                                  figsize=(8,5),
                                                                  fontsize=12,
                                                                  linewidth=1.5,
                                                                  marker='o')
 
                ax.set_xticks(dTable[table].index)
                ax.set_xticklabels(fcts)
       
                ename = table.split('_')[0][4:]

                ax.legend([ename])
            
                plt.ylabel(Stat)
                plt.xlabel('Horas de Integração')
                plt.xticks(rotation=90)
      
                if Stat == 'ACOR':
                    plt.axhline(y=0.5, color='black', linestyle='-', linewidth=1)
                else:
                    plt.axhline(y=0.0, color='black', linestyle='-', linewidth=1)
  
                plt.grid(color='grey', linestyle='--', linewidth=0.5)
 
                if saveFig:            
                    #fig_name = table.replace(str(tExt),'') + Vars[var][0] + '.png'
                    if tExt == 'scan':
                        fig_name = table.replace('T.'+str(tExt),'') + '_' + Vars[var][0].replace(':','') + '.png'
                    else:
                        fig_name = table.replace('T.'+str(tExt),'') + '_' + Vars[var][0].replace('-','') + '.png'
                    plt.savefig(os.path.join(figDir, fig_name), bbox_inches='tight', dpi=120)
                
            if showFig:
                plt.show()

            plt.close()
        
    return

def plot_lines_tStudent(dataInicial,dataFinal,dTable_series,Exps,Var,VarName,ldrom_exp,ldrosup_exp,ldroinf_exp,varlev_exps,outDir,**kwargs):
        
    """
    plot_lines_tStudent
    ===================
    
    Esta função plota gráficos de linha acompanhados dos resultados do teste de significância t-Student.
    Os gráficos são plotados apenas com base nas tabelas de correlação de anomalia do SCANTEC.
    
    Parâmetros de entrada
    ---------------------
        Exps        : lista com os nomes dos experimentos;
        ldrom_exp   : curva do teste referente ao experimento;
        ldrosup_exp : limite superior do teste;
        ldroinf_exp : limite inferior do teste;
        varlev_exps : dataframes com as variáveis dos experimentos.
    
    Parâmetros de entrada opcionais
    -------------------------------
        showFig : valor Booleano para mostrar ou não as figuras durante a plotagem:
                  * showFig=False (valor padrão), não mostra as figuras (mais rápido);
                  * showFig=True, mostra as figuras (mais lento);
        saveFig : valor Booleano para salvar ou não as figuras durante a plotagem:
                  * saveFig=False (valor padrão), não salva as figuras;
                  * saveFig=True, salva as figuras;
        figDir  : string com o diretório onde as figuras serão salvas.

    Resultado
    ---------
        Resultado do teste de significância e valores críticos para serem utilizados pela função
        plot_lines_tStudent. Figuras salvas no diretório definido na variável outDir ou figDir. 
        Se figDir não for passado, então as figuras são salvas no diretório outDir (SCANTEC/dataout).
    
    Uso
    ---
        import scanplot 
        
        data_vars, data_conf = scanplot.read_namelists("~/SCANTEC")
        
        dataInicial = data_conf["Starting Time"]
        dataFinal = data_conf["Ending Time"]
        Vars = list(map(data_vars.get,[*data_vars.keys()]))
        Stats = ["ACOR", "RMSE", "VIES"]
        Exps = list(data_conf["Experiments"].keys())
        outDir = data_conf["Output directory"]
       
        Var = Vars[0][0].lower()
        VarName = Vars[0][1]
 
        dTable = scanplot.get_dataframe(dataInicial,dataFinal,Stats,Exps,outDir,series=False)

        dTable_series = scanplot.get_dataframe(dataInicial,dataFinal,Stats,Exps,outDir,series=True)

        varlev_exps = scanplot.concat_tables_and_loc(dTable,dataInicial,dataFinal,Exps,series=False)
       
        varlev_dia_exps = scanplot.concat_tables_and_loc(dTable_series,dataInicial,dataFinal,Exps,Var,series=True)
 
        lst_varlev_dia_exps_rsp = scanplot.df_fill_nan(varlev_exps,varlev_dia_exps)
        
        ldrom_exp, ldrosup_exp, ldroinf_exp = scanplot.calc_tStudent(lst_varlev_dia_exps_rsp)
        
        scanplot.plot_lines_tStudent(dataInicial,dataFinal,dTable_series,Exps,Var,VarName,ldrom_exp,
                                     ldrosup_exp,ldroinf_exp,varlev_exps,outDir,
                                     figDir=figDir,saveFig=True,showFig=True)

    Observações
    -----------
        * Experimental, esta função necessita ser validada;
        * Na presente versão, apenas uma variável e nível pode ser plotada. 
    """        

    # tExt é uma variável global e o seu valor é sempre atualizado
    global tExt

#    # Verifica se foram passados os argumentos opcionais e atribui os valores
#    if 'combine' in kwargs:
#        combine = kwargs['combine']
#    else:
#        combine = gvars.combine

    if 'tExt' in kwargs:
        tExt = kwargs['tExt']      
        # Atualiza o valor global de tExt
        gvars.tExt = tExt
    else:
        tExt = gvars.tExt

    if 'figDir' in kwargs:
        figDir = kwargs['figDir']
        # Verifica se o diretório figDir existe e cria se necessário
        if not os.path.exists(figDir):
            os.makedirs(figDir)
    else:
        figDir = outDir

    if 'showFig' in kwargs:
        showFig = kwargs['showFig']
    else:
        showFig = gvars.showFig

    if 'saveFig' in kwargs:
        saveFig = kwargs['saveFig']
    else:
        saveFig = gvars.saveFig

    if 'lineStyles' in kwargs:
        lineStyles = kwargs['lineStyles']
        colors = lineStyles    
    else:
        lineStyles = gvars.lineStyles
        colors = ['black', 'red', 'green', 'blue', 'orange', 'brown', 'cyan', 'magenta']

    if isnotebook(get_ipython().__class__.__name__):
        if showFig:
            ipython.magic('matplotlib inline')           
            mpl.rcParams.update({'figure.max_open_warning': 0})
        else:
            ipython.magic('matplotlib agg')           
    else:
        if not showFig:
            mpl.use('agg')
            mpl.rcParams.update({'figure.max_open_warning': 0})

    # Ignore Seaborn and respect rcParams
    sns.reset_orig()    
   
    datai = dataInicial.strftime('%Y%m%d%H')
    dataf = dataFinal.strftime('%Y%m%d%H')
 
    fig, axs = plt.subplots(2, sharex=True, sharey=False, gridspec_kw={'hspace': 0}, figsize = (8,6))
    
    j = 0
   
    # Curvas da correlação de anomalias 
    for i, varlev_exp in enumerate(varlev_exps):
        if i == 0:
            axs[0].plot(varlev_exp, color=colors[j], linestyle='--', label=str(Exps[j]), linewidth=1.5)
        else:
            axs[0].plot(varlev_exp, color=colors[j], label=str(Exps[j]), linewidth=1.5)
          
        axs[0].grid(color='grey', linestyle='--', linewidth=0.5)
        axs[0].legend()
        
        j += 1
        
    j = 1
        
    # Curvas do teste t-Student
    for drosup_exp, droinf_exp, drom_exp in zip(ldrosup_exp,ldroinf_exp,ldrom_exp):
        
        axs[1].bar(range(0, len(drosup_exp)), drosup_exp, color=(0, 0, 0, 0), edgecolor=colors[j], align='center', linestyle='-', linewidth=1.5)
        axs[1].bar(range(0, len(droinf_exp)), droinf_exp, color=(0, 0, 0, 0), edgecolor=colors[j], align='center', linestyle='-', linewidth=1.5)
        
        axs[1].plot(drom_exp, color=colors[j])

        j += 1
        
    axs[1].axhline(color='black', linewidth=0.5)
    axs[1].grid(color='grey', linestyle='--', linewidth=0.5)
        
    for ax in axs:
        ax.label_outer()        

    axs[0].axhline(y=0.5, color='black', linestyle='-', linewidth=1)

    axs[0].set_title(str(VarName))
    axs[1].set_xlabel('Horas de Integração')
    axs[0].set_ylabel('ACOR')
    axs[1].set_ylabel('Valor Crítico')        
    plt.xticks(rotation=90)

    axs[1].text(0.01, 0.93, "Diferença em relação a " + Exps[0], transform=ax.transAxes);
    axs[1].text(0.01, 0.18, "Diferenças na ACOR possuem significância", transform=ax.transAxes);
    axs[1].text(0.01, 0.10, "de 95% quando as curvas estão fora das", transform=ax.transAxes);
    axs[1].text(0.01, 0.02, "suas respectivas barras", transform=ax.transAxes);

    fcts = dTable_series[list(dTable_series.keys())[0]].loc[:,"%Previsao"].values
    axs[1].set_xticks(dTable_series[list(dTable_series.keys())[0]].index)
    axs[1].set_xticklabels(fcts)

    if saveFig:            
        #fig_name = 'ACOREXPS' + str(datai) + str(dataf) + '_' + Var.replace(':','').upper() + '-' + 'tStudent.png'
        if tExt == 'scan':
            fig_name = 'ACOREXPS_' + str(datai) + str(dataf) + '_' + Var.replace(':','').upper() + '-' + 'tStudent.png'
        else:
            fig_name = 'ACOREXPS_' + str(datai) + str(dataf) + '_' + Var.replace('-','').upper() + '-' + 'tStudent.png'
        plt.savefig(os.path.join(figDir, fig_name), bbox_inches='tight', dpi=120)

    if showFig:
        plt.show()
    else:
        plt.close()

    return

def plot_scorecard(dTable,Vars,Stats,Tstat,Exps,outDir,**kwargs):
    
    """
    plot_scorecard
    ==============
    
    Esta função calcula o "Ganho Percentual*" e a "Mudança Fracional*" a partir 
    das estatísticas do SCANTEC e plota os resultados na forma de um scorecard. 
    São necessários dois experimentos.
    
    *Banos et al., 2018: Impacto da Assimilação de Perfis de Refratividade do 
                         Satélite Metop-B nas Previsões de Tempo do CPTEC/INPE 
                         Durante os Meses de Janeiro e Agosto de 2014.
    
    Parâmetros de entrada
    ---------------------
        dTable : objeto dicionário com uma ou mais tabelas do SCANTEC;
        Vars   : lista com os nomes e níveis das variáveis;
        Stats  : lista com os nomes das estatísticas a serem processadas;
        Tstat  : tipo de score a ser calculado;
        outDir : string com o diretório com as tabelas do SCANTEC.
    
    Parâmetros de entrada opcionais
    -------------------------------
        showFig : valor Booleano para mostrar ou não as figuras durante a plotagem:
                  * showFig=False (valor padrão), não mostra as figuras (mais rápido);
                  * showFig=True, mostra as figuras (mais lento);
        saveFig : valor Booleano para salvar ou não as figuras durante a plotagem:
                  * saveFig=False (valor padrão), não salva as figuras;
                  * saveFig=True, salva as figuras;
        figDir  : string com o diretório onde as figuras serão salvas;
        tExt    : string com o extensão dos nomes das tabelas do SCANTEC:
                  * tExt='scan' (valor padrão), considera as tabelas do SCANTEC;
                  * tExt='scam', considera os nomes das tabelas das versões antigas do SCANTEC.

    Resultado
    ---------
        Figuras salvas no diretório definido na variável outDir ou figDir. Se figDir não
        for passado, então as figuras são salvas no diretório outDir (SCANTEC/dataout).
    
    Uso
    ---
        import scanplot 
        
        data_vars, data_conf = scanplot.read_namelists("~/SCANTEC")
        
        dataInicial = data_conf["Starting Time"]
        dataFinal = data_conf["Ending Time"]
        Vars = list(map(data_vars.get,[*data_vars.keys()]))
        Stats = ["ACOR", "RMSE", "VIES"]

        Exps = ["EXP1", "EXP2"]

        outDir = data_conf["Output directory"]

        figDir = data_conf["Output directory"]
        
        dTable = scanplot.get_dataframe(dataInicial,dataFinal,Stats,Exps,outDir)
        
        scanplot.plot_scorecard(dTable,Vars,Stats,'ganho',Exps,outDir,figDir=figDir,showFig=True,saveFig=True)

    Observações
    -----------
        Nos scorecards, as cores sempre indicam os ganhos do segundo experimento com relação ao primeiro.
        Portanto, os tons mais intensos de verde, indicam que o 'EXP2' apresentam maior ganho em relação 
        ao 'EXP1' ou que a mudança fracional é maior.
    """

    if not len(Exps) == 2:
        raise Exception('Para utilizar a função plot_scorecard, são necessários 2 experimentos.')

    # Verifica se foram passados os argumentos opcionais e atribui os valores

    global tExt

    if 'tExt' in kwargs:
        tExt = kwargs['tExt']      
        # Atualiza o valor global de tExt
        gvars.tExt = tExt
    else:
        tExt = gvars.tExt

    if 'figDir' in kwargs:
        figDir = kwargs['figDir']
    else:
        figDir = outDir

    if 'showFig' in kwargs:
        showFig = kwargs['showFig']
    else:
        showFig = gvars.showFig

    if 'saveFig' in kwargs:
        saveFig = kwargs['saveFig']
    else:
        saveFig = gvars.saveFig

    if isnotebook(get_ipython().__class__.__name__):
        if showFig:
            ipython.magic('matplotlib inline')           
            mpl.rcParams.update({'figure.max_open_warning': 0})
        else:
            ipython.magic('matplotlib agg')           
    else:
        if not showFig:
            mpl.use('agg')
            mpl.rcParams.update({'figure.max_open_warning': 0})

    if tExt == 'scan': 
        list_var = [ltuple[0].lower() for ltuple in Vars]
    else:
        list_var = [ltuple[0] for ltuple in Vars]

    for Stat in Stats:
        Tables = list(filter(lambda x:Stat in x, [*dTable.keys()]))
    
        exp1 = [s for s in Tables if Exps[0] in s][0]
        exp2 = [s for s in Tables if Exps[1] in s][0]
    
        p_table1 = pd.pivot_table(dTable[exp1], index="%Previsao", values=list_var)
        p_table2 = pd.pivot_table(dTable[exp2], index="%Previsao", values=list_var)
 
        if Tstat == "ganho":
            # Porcentagem de ganho
            if Stat == "ACOR":
                score_table = ((p_table2[1:].T - p_table1[1:].T) / (1.0 - p_table1[1:].T)) * 100
            elif Stat == "RMSE" or Stat == "VIES":
                score_table = ((p_table2[1:].T - p_table1[1:].T) / (0.0 - p_table1[1:].T)) * 100
        elif Tstat == "fc":
            # Mudança fracional
            score_table = (1.0 - (p_table2[1:].T / p_table1[1:].T))

        # Tentativa de substituir os NaN - que aparecem quando vies e rmse são iguais a zero
        score_table = score_table.fillna(0.0000001)

        # Figura
        plt.figure(figsize = (15,10))
        
        sns.set(style="whitegrid", font_scale=0.90)
        sns.set_context(rc={"xtick.major.size":  1.5,  "ytick.major.size": 1.5,
                            "xtick.major.pad":   0.05,  "ytick.major.pad": 0.05,
                            "xtick.major.width": 0.5, "ytick.major.width": 0.5,
                            "xtick.minor.size":  1.5,  "ytick.minor.size": 1.5,
                            "xtick.minor.pad":   0.05,  "ytick.minor.pad": 0.05,
                            "xtick.minor.width": 0.5, "ytick.minor.width": 0.5})
 
        if Tstat == "ganho":
            ax = sns.heatmap(score_table, annot=True, fmt="1.0f", cmap="RdYlGn", 
                               vmin=-100, vmax=100, center=0, linewidths=0.25, square=False,
                               cbar_kws={"shrink": 1.0, 
                                         "ticks": np.arange(-100,110,10),
                                         "pad": 0.01,
                                         "orientation": "vertical"})
 
            cbar = ax.collections[0].colorbar
            cbar.set_ticks([-100, -50, 0, 50, 100])
            cbar.set_ticklabels(["pior", "-50%", "0", "50%", "melhor"])
            cbar.ax.tick_params(labelsize=12)    
                
            plt.title("Ganho " + str(Stat) + " (%) - " + str(Tables[0][9:19]) + "-" + str(Tables[0][19:29]) + "\n" + Exps[0] + " Vs. " + Exps[1], fontsize=14)
            
            fig = ax.get_figure()
 
        elif Tstat == "fc":
            ax = sns.heatmap(score_table, annot=True, fmt="1.0f", cmap="RdYlGn", 
                               vmin=-1, vmax=1, center=0, linewidths=0.25, square=False,
                               cbar_kws={"shrink": 1.0, 
                                         "ticks": np.arange(-1,2,1),
                                         "pad": 0.01,
                                         "orientation": "vertical"})
 
            cbar = ax.collections[0].colorbar
            cbar.set_ticks([-1, -0.5, 0, 0.5, 1])
            cbar.set_ticklabels(["pior", "-0.5", "0", "0.5", "melhor"])
            cbar.ax.tick_params(labelsize=12)    
 
            plt.title("Mudança Fracional " + str(Stat) + " - " + str(Tables[0][9:19]) + "-" + str(Tables[0][19:29]) + "\n" + Exps[0] + " Vs. " + Exps[1], fontsize=14)
   
            fig = ax.get_figure()

        plt.xlabel("Horas de Integração")
        plt.yticks(fontsize=12)
        plt.xticks(rotation=90, fontsize=12)
    
        plt.figure()
        plt.tight_layout()

        if saveFig:
            fig_name = "SCORECARD_" + str(Tstat).upper() + "_" + str(Stat) + "_" + str(Exps[0]) + "_" + str(Exps[1]) + "_" + str(Tables[0][9:19]) + str(Tables[0][19:29]) + ".png"

            fig.savefig(os.path.join(figDir, fig_name), bbox_inches="tight", dpi=120)
        
        plt.close()
    
        if showFig:
            plt.show()
        
    return

def plot_dTaylor(dTable,data_conf,Vars,Stats,outDir,**kwargs):
    
    """
    plot_dTaylor
    ============
    
    Esta função plota o diagrama de Taylor a partir das tabelas de estatísticas
    do SCANTEC, para um ou mais experimentos.
    
    Esta função utiliza o módulo SkillMetrics (https://pypi.org/project/SkillMetrics/). 
    
    Parâmetros de entrada
    ---------------------
        dTable    : objeto dicionário com uma ou mais tabelas do SCANTEC;
        Vars      : lista com os nomes e níveis das variáveis;
        data_conf : objeto dicionário com as configurações do SCANTEC;
        Stats     : lista com os nomes das estatísticas a serem processadas
                    (são necessárias as tabelas ACOR, RMSE e VIES);
        outDir    : string com o diretório com as tabelas do SCANTEC.
    
    Parâmetros de entrada opcionais
    -------------------------------
        showFig : valor Booleano para mostrar ou não as figuras durante a plotagem:
                  * showFig=False (valor padrão), não mostra as figuras (mais rápido);
                  * showFig=True, mostra as figuras (mais lento);
        saveFig : valor Booleano para salvar ou não as figuras durante a plotagem:
                  * saveFig=False (valor padrão), não salva as figuras;
                  * saveFig=True, salva as figuras;
        figDir  : string com o diretório onde as figuras serão salvas.

    Resultado
    ---------
        Figuras salvas no diretório definido na variável outDir ou figDir. Se figDir não
        for passado, então as figuras são salvas no diretório outDir (SCANTEC/dataout).
    
    Uso
    ---
        import scanplot 
        
        data_vars, data_conf = scanplot.read_namelists("~/SCANTEC")
        
        dataInicial = data_conf["Starting Time"]
        dataFinal = data_conf["Ending Time"]
        Vars = list(map(data_vars.get,[*data_vars.keys()]))
        Stats = ["ACOR", "RMSE", "VIES"]
        Exps = list(data_conf["Experiments"].keys())
        outDir = data_conf["Output directory"]
        
        figDir = data_conf["Output directory"]

        dTable = scanplot.get_dataframe(dataInicial,dataFinal,Stats,Exps,outDir)
        
        scanplot.plot_dTaylor(dTable,data_conf,Vars,Stats,outDir,figDir=figDir,showFig=True,saveFig=True)       
 
    Observações
    -----------
        Experimental, esta função considera o devio-padrão como a raiz quadrada do RMSE.
    """
    
    # Verifica se foram passados os argumentos opcionais e atribui os valores

    if 'tExt' in kwargs:
        tExt = kwargs['tExt']      
        # Atualiza o valor global de tExt
        gvars.tExt = tExt
    else:
        tExt = gvars.tExt

    if 'figDir' in kwargs:
        figDir = kwargs['figDir']
    else:
        figDir = outDir

    if 'showFig' in kwargs:
        showFig = kwargs['showFig']
    else:
        showFig = gvars.showFig

    if 'saveFig' in kwargs:
        saveFig = kwargs['saveFig']
    else:
        saveFig = gvars.saveFig

    if isnotebook(get_ipython().__class__.__name__):
        if showFig:
            ipython.magic('matplotlib inline')           
            mpl.rcParams.update({'figure.max_open_warning': 0})
        else:
            ipython.magic('matplotlib agg')           
    else:
        if not showFig:
            mpl.use('agg')
            mpl.rcParams.update({'figure.max_open_warning': 0})

    dataInicial = data_conf["Starting Time"]
    dataFinal = data_conf["Ending Time"]

    datai = dataInicial.strftime('%Y%m%d%H')
    dataf = dataFinal.strftime('%Y%m%d%H')

    # Ignore Seaborn and respect rcParams
    sns.reset_orig()
    
    # Set the figure properties (optional)
    rcParams["figure.figsize"] = [8.0, 6.5]
    rcParams['lines.linewidth'] = 1 # line width for plots
    rcParams.update({'font.size': 12}) # font size of axes text
    rcParams['axes.titlepad'] = 40 # title vertical distance from plot
    
    Exps = [*data_conf['Experiments'].keys()]
    
    fig = plt.figure()
       
    for exp in range(len(Exps)): 
        
        for var in range(len(Vars)):
        
            tAcor = list(filter(lambda x:'ACOR' in x, [*dTable.keys()]))[exp]
            tRmse = list(filter(lambda x:'RMSE' in x, [*dTable.keys()]))[exp]
            tVies = list(filter(lambda x:'VIES' in x, [*dTable.keys()]))[exp]
    
            bias  = dTable[tVies].loc[:,[Vars[var][0].lower()]].to_numpy()
            ccoef = dTable[tAcor].loc[:,[Vars[var][0].lower()]].to_numpy()
            crmsd = dTable[tRmse].loc[:,[Vars[var][0].lower()]].to_numpy()
            sdev  = (dTable[tRmse].loc[:,[Vars[var][0].lower()]]**(1/2)).to_numpy() # rever

            biasT = bias.T
            ccoefT = ccoef.T
            crmsdT = crmsd.T
            sdevT = sdev.T
    
            bias = np.squeeze(biasT)
            ccoef = np.squeeze(ccoefT)
            crmsd = np.squeeze(crmsdT)
            sdev = np.squeeze(sdevT)
    
            label = [*dTable[tVies].loc[:,"%Previsao"].values]
        
            if not showFig:
                plt.figure()    

            plt.tight_layout()
    
            sm.taylor_diagram(sdev, crmsd, ccoef, markerLabel = label, 
                              locationColorBar = 'EastOutside',
                              markerDisplayed = 'colorBar', titleColorBar = 'Bias',
                              markerLabelColor='black', markerSize=10,
                              markerLegend='off', cmapzdata=bias,
                              colRMS='g', styleRMS=':',  widthRMS=2.0, titleRMS='on',
                              colSTD='b', styleSTD='-.', widthSTD=1.0, titleSTD ='on',
                              colCOR='k', styleCOR='--', widthCOR=1.0, titleCOR='on')
        
            plt.title("Diagrama de Taylor " + str(Exps[exp]) + '\n' + str(Vars[var][1]), fontsize=14)

            if saveFig:
                #fig_name = 'dtaylor-' + str(Exps[exp]) + '-' + Vars[var][0] + '.png'
                if tExt == 'scan':
                    fig_name = 'DTAYLOR_' + str(Exps[exp]) + '_' + str(datai) + str(dataf) + '_' + Vars[var][0].replace(':', '') + '.png'
                else:
                    fig_name = 'DTAYLOR_' + str(Exps[exp]) + '_' + str(datai) + str(dataf) + '_' + Vars[var][0].replace('-','') + '.png'
                plt.savefig(os.path.join(figDir, fig_name), bbox_inches="tight", dpi=120)

            if showFig:
                plt.show()
            else:
                plt.close(fig)     

    plt.close(fig)     

    return

def plot_fields(dSet,Vars,Stats,outDir,**kwargs):

    """
    plot_fields
    ===========
    
    Esta função plota gráficos espaciais a partir de um dicionário de dataarrays com os arquivos binários do SCANTEC.
    
    Parâmetros de entrada
    ---------------------
        dSet   : objeto dicionário com uma ou mais arquivos binários do SCANTEC;
        Vars   : lista com os nomes e níveis das variáveis;
        Stats  : lista com os nomes das estatísticas a serem processadas;
        outDir : string com o diretório com os arquivos binários do SCANTEC.

    Parâmetros de entrada opcionais
    -------------------------------
        showFig    : valor Booleano para mostrar ou não as figuras durante a plotagem
                     showFig=False (valor padrão), não mostra as figuras (mais rápido)
                     showFig=True, mostra as figuras (mais lento);
        saveFig    : valor Booleano para salvar ou não as figuras durante a plotagem:
                     * saveFig=False (valor padrão), não salva as figuras;
                     * saveFig=True, salva as figuras;
        lineStyles : lista com as cores e os estilos das linhas (o número de elementos
                     da lista deve ser igual ao número de experimentos);
        figDir     : string com o diretório onde as figuras serão salvas;
        combine    : valor Booleano para combinar os campos das estatísticas dos experimentos em um só gráfico:
                     * combine=False (valor padrão), plota os campos em gráficos separados;
                     * combine=True, plota os campos das mesmas estatísticas no mesmo gráfico (painel);
        tExt       : string com o extensão dos nomes das tabelas do SCANTEC:
                     * tExt='scan' (valor padrão), considera os arquivos binários do SCANTEC;
                     * tExt='scam', considera os nomes dos arquivos binários das versões antigas do SCANTEC.
        hvplot     : valor Booleano para apresentar utilizar o hvplot (holoviews) e controlar o loop temporal das figuras por meio de widgets
                     * hvplot=False (valor padrão), apresenta os campos como um painel
                     * hvplot=True, apresenta os campos como um loop controlado por widgets

    Resultado
    ---------
        Figuras salvas no diretório definido na variável outDir ou figDir. Se figDir não
        for passado, então as figuras são salvas no diretório outDir (SCANTEC/dataout).
    
    Uso
    ---
        import scanplot 
        
        data_vars, data_conf = scanplot.read_namelists("~/SCANTEC")
        
        dataInicial = data_conf["Starting Time"]
        dataFinal = data_conf["Ending Time"]
        Vars = list(map(data_vars.get,[*data_vars.keys()]))
        Stats = ["ACOR", "RMSE", "VIES"]
        Exps = list(data_conf["Experiments"].keys())
        outDir = data_conf["Output directory"]
       
        figDir = data_conf["Output directory"]
 
        lineStyles = ['k-', 'b-', 'b--', 'r-', 'r--']

        dSet = scanplot.get_dataset(data_conf,data_vars,Stats,Exps,outDir)

        scanplot.plot_fields(dSet,Vars,Stats,outDir,showFig=True,saveFig=True,lineStyles=lineStyles,figDir=figDir)
    """
  
    # tExt é uma variável global e o seu valor é sempre atualizado
    global tExt

    # Verifica se foram passados os argumentos opcionais e atribui os valores
    if 'combine' in kwargs:
        combine = kwargs['combine']
    else:
        combine = gvars.combine

    if 'tExt' in kwargs:
        tExt = kwargs['tExt']      
        # Atualiza o valor global de tExt
        gvars.tExt = tExt
    else:
        tExt = gvars.tExt

    if 'figDir' in kwargs:
        figDir = kwargs['figDir']
        # Verifica se o diretório figDir existe e cria se necessário
        if not os.path.exists(figDir):
            os.makedirs(figDir)
    else:
        figDir = outDir

    if 'showFig' in kwargs:
        showFig = kwargs['showFig']
    else:
        showFig = gvars.showFig

    if 'saveFig' in kwargs:
        saveFig = kwargs['saveFig']
    else:
        saveFig = gvars.saveFig

    if 'lineStyles' in kwargs:
        lineStyles = kwargs['lineStyles']
    else:
        lineStyles = gvars.lineStyles

    if 'hvplot' in kwargs:
        hvplot = kwargs['hvplot']
    else:
        hvplot = gvars.hvplot

    if 'avaltype' in kwargs:
        avaltype = kwargs['avaltype']
    else:
        avaltype = gvars.avaltype


    # Opção combine=True    
    if combine and hvplot:
    
        if isnotebook(get_ipython().__class__.__name__): # seções iterativas
            if showFig:
                ipython.magic('matplotlib inline')           
                #mpl.rc('figure', max_open_warning = 0)
                mpl.rcParams.update({'figure.max_open_warning': 0})
            else:
                ipython.magic('matplotlib agg')           
        else: # seções não iterativas
            if not showFig:
                mpl.use('agg')
                mpl.rcParams.update({'figure.max_open_warning': 0})

        #print('combine=True and hvplot=True')

        def display_field(filename, variable, time):
            tmp = dSet[filename][variable].isel(time=time).load()
            return tmp.hvplot.contourf(colorbar=True, coastline=True, global_extent=True, frame_height=450, 
                                       crs=ccrs.PlateCarree(), projection=ccrs.PlateCarree(), levels=10)
        
        filenames = list(dSet.keys())
        variables = list(dSet[filenames[0]].data_vars)
        times = list(dSet[filenames[0]].time.values)
        
        class SDDisplay(param.Parameterized):
            variable  = param.Selector(default=variables[0], objects=variables)
            filename  = param.Selector(default=filenames[0], objects=filenames)
            time      = param.Integer(default=0, bounds=(0, len(times)-1))
        
            def view(self):
                return display_field(self.filename, self.variable, self.time)
            
        obj = SDDisplay()
        
        title = "## Distribuição Espacial das Estatísticas\nAjuste os parâmetros abaixo para mostrar o gráfico."

        SDDisplay(name='SDDisplay', filename=filenames[0], variable=variables[0], time=0)

        return pn.Column(avaltype, title, pn.Row(obj.param, obj.view))
        #return pn.Column(title, pn.Row(obj.param, obj.view))

    elif combine and not hvplot:

        if isnotebook(get_ipython().__class__.__name__): # seções iterativas
            if showFig:
                ipython.magic('matplotlib inline')           
                #mpl.rc('figure', max_open_warning = 0)
                mpl.rcParams.update({'figure.max_open_warning': 0})
            else:
                ipython.magic('matplotlib agg')           
        else: # seções não iterativas
            if not showFig:
                mpl.use('agg')
                mpl.rcParams.update({'figure.max_open_warning': 0})

        #print('combine=True and hvplot=False')

    elif not combine and hvplot:

        if isnotebook(get_ipython().__class__.__name__): # seções iterativas
            if showFig:
                ipython.magic('matplotlib inline')           
                #mpl.rc('figure', max_open_warning = 0)
                mpl.rcParams.update({'figure.max_open_warning': 0})
            else:
                ipython.magic('matplotlib agg')           
        else: # seções não iterativas
            if not showFig:
                mpl.use('agg')
                mpl.rcParams.update({'figure.max_open_warning': 0})

        #print('combine=False and hvplot=True')

        def plot(fname, var, title):
            return dSet[fname][var].hvplot.contourf(groupby='time', title=title, colorbar=True, coastline=True, 
                                                    global_extent=True, frame_height=100, crs=ccrs.PlateCarree(),
                                                    projection=ccrs.PlateCarree(), levels=10)

        def playout(obj_lst):
                layout = hv.Layout(fld_obj_lst).cols(3)
                hv_panel = pn.panel(layout)
                return pn.panel(layout, center=True, widget_type='scrubber', widget_location='top')

        fnames = list(dSet.keys())

        for fname in fnames:

            fld_obj_lst = []
            for var in list(dSet[fnames[0]].data_vars):

                title = fname.split('_')[0][0:4] + ' ' + fname.split('_')[0][4:]  + ' ' + var

                fld_obj = plot(fname, var, title)        

                fld_obj_lst.append(fld_obj)

                fld_pnl = playout(fld_obj_lst)

            return fld_pnl

    # Opção combine=False (padrão)
    else:
            
        if isnotebook(get_ipython().__class__.__name__):
            if showFig:
                ipython.magic('matplotlib inline')           
                mpl.rcParams.update({'figure.max_open_warning': 0})
            else:
                ipython.magic('matplotlib agg')           
        else:
            if not showFig:
                mpl.use('agg')
                mpl.rcParams.update({'figure.max_open_warning': 0})

        #print('combine=False and hvplot=False') # Faz um loop simples dentro do dicionário para plotar todas as figuras

        # Ref.: https://github.com/pydata/xarray/issues/619#issuecomment-459888596
        def make_colorbar(ax, mappable, **kwargs):
            from mpl_toolkits.axes_grid1 import make_axes_locatable
            import matplotlib as mpl
        
            divider = make_axes_locatable(ax)
            orientation = kwargs.pop('orientation', 'vertical')
            if orientation == 'vertical':
                loc = 'right'
            elif orientation == 'horizontal':
                loc = 'bottom'
                
            cax = divider.append_axes(loc, '5%', pad='3%', axes_class=mpl.pyplot.Axes)
            ax.get_figure().colorbar(mappable, cax=cax, orientation=orientation)

        for file in list(dSet.keys()):

            ntime = len(dSet[file].time)-1

            for time in range(ntime):

                for var in list(dSet[file].data_vars):

                    file_s = file.split('_')
                    file_p1 = file_s[0]
                    file_p2 = file_s[1].split('F.scan')[0]
        
                    stat = file_p1[0:4]
                    exp = file_p1[4:8]
        
                    datai = file_p2[0:10]
                    dataf = file_p2[10:20]
        
                    stime = dSet[file][var].isel(time=time).coords['time'].values
                    pd_stime = pd.to_datetime(str(stime)) 
                    ftime = pd_stime.strftime('%Y-%m-%d-%H')

                    # Tamanho da figura
                    plt.figure(figsize=(10,9))

                    # Projeção
                    ax = plt.subplot(projection=ccrs.PlateCarree())

                    # Plota
                    im = dSet[file][var].isel(time=time).plot.contourf(ax=ax, 
                                                                      transform=ccrs.PlateCarree(),
                                                                      add_colorbar=False)
                    
                    # Linhas de grade, costa e rótulos 
                    gl = ax.gridlines(color='grey', linestyle='--', linewidth=0.5, draw_labels=True) 
                    gl.xlabels_top, gl.ylabels_right = False, False
                    #gl.toplabels_top, gl.rightlabels_right = False, False
                    ax.coastlines()
                    ax.set_aspect('equal') 

                    # Barra de cores 
                    make_colorbar(ax, im, orientation='vertical')

                    # Título
                    ax.set_title(stat + ' ' + exp + ' ' + var + ' (' + ftime + ')')

                    # Se saveFig=True
                    if saveFig: 
                        fig_name = stat + '_' + exp + '_' + var + '-' + ftime  + str('.png')
                        plt.savefig(os.path.join(figDir, fig_name), bbox_inches='tight', dpi=120)

                    if showFig:
                        plt.draw()
                    else:
                        plt.close() 

        return pn
