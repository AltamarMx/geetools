# %load ../iertools/read.py
import sqlite3 as sql
import pandas as pd
import matplotlib.pyplot as plt
import warnings


import sqlite3 as sql
import pandas as pd
import matplotlib.pyplot as plt
import warnings


class read_sql:
    """
    Read the SQL output of energyplus file, it's able to extract output variables reported by energyplus simulation or construction systems of the model
    Arguments:
    ----------
    file -- path location of SQL file
    read -- mode of reading, initial options: "all" and "constructions"
    cols_json -- json file to rename the columns
    
    Properties:
    data -- pandas dataframe with data extracted of SQL file
    variables -- name of variables using energyplus notation
    vars -- ??
    vars_numbered -- ??
    mlc -- ??
    construction_systems -- Construction Systems found inside SQL file
    """

    def __init__(self,file,cols_json=None,alias=False):
        """
        Read the SQL output of energyplus file
        """
        self.myconn = sql.connect(file)
        # if (read=="data") or (read=="all"):
        command = "SELECT ReportDataDictionaryIndex, KeyValue, Name, Units FROM ReportDataDictionary"
        variables = pd.read_sql_query(command,con=self.myconn)

        variables['variable_name'] = variables.KeyValue + ':' + variables.Name + ' (' + variables.Units + ')'
        #self.variables = variables
        
        self.vars = variables.variable_name.unique()
        vars = variables.variable_name.unique()
        self.vars_numbered = [i for i in enumerate(self.vars)]
        
        command = "SELECT tm.TimeIndex, tm.Year, tm.Month, tm.Day, tm.Hour, tm.Minute FROM Time AS tm"
        time = pd.read_sql_query(command,con=self.myconn)
        time = time[time.Year!=0]
        command = """SELECT ReportData.TimeIndex, ReportData.ReportDataDictionaryIndex, ReportData.Value
          FROM (ReportData INNER JOIN ReportDataDictionary ON ReportData.ReportDataDictionaryIndex = ReportDataDictionary.ReportDataDictionaryIndex) 
          INNER JOIN Time ON ReportData.TimeIndex = Time.TimeIndex"""
        data = pd.read_sql_query(command,con=self.myconn)
        data_variables = pd.merge(data,variables)
        data_variables_time = pd.merge(data_variables,time)
        df = data_variables_time.copy()
        
        df['date'] = pd.to_datetime(df[['Year','Month','Day','Hour','Minute']])
        df['variable_name'] = df.KeyValue + ':' + df.Name + ' (' + df.Units + ')'
        df  = df.pivot_table(index="date", columns="variable_name", values="Value")
        
        self.data = df
    
        
        # if (read=="construction") or (read=="all"):
#             print("aca")
        command = """SELECT * FROM  Materials """
        m       = pd.read_sql_query(command,con=self.myconn)
        m = m.rename(columns={'Name': 'NameMaterial'})
        # 
        command = """SELECT * FROM  Constructions """
        c = pd.read_sql_query(command,con=self.myconn)
        c = c.rename(columns={'Name': 'NameConstruction'})
        # 
        command = """SELECT * FROM  ConstructionLayers """
        l = pd.read_sql_query(command,con=self.myconn)
        ml   = pd.merge(m,l)
        mlc = pd.merge(ml,c)
        self.mlc = mlc
        self.construction_systems = mlc.NameConstruction.unique()
        self.myconn.close()

        variables = self.vars
        cols_json = {}
        for variable in variables:
            cols_json.update({variable:variable})
            
        if alias:
            read_sql.__rename(cols_json)
            read_sql.rename(self,columns = cols_json)
            
        # self.names = cols_json
        # print(cols_json)
        self.vars_dict = cols_json
    
    def rename(self,columns,inplace=True):
        self.data.rename(columns=columns,inplace=True)
        self.vars = self.data.columns
        self.vars_numbered = [i for i in enumerate(self.vars)]
    def __rename(cols_json):
        variables  = cols_json.keys()
        for variable in variables:
            try:
                if "Zone Mean Air Temperature" in variable:
                    Ti_variables = "Ti_" + variable.split(":")[0].replace(" ","")
                    cols_json[variable] = Ti_variables
                if "Site Outdoor Air Dry" in variable:
                    cols_json[variable] = "To"
                if "Wind Speed" in variable:
                    cols_json[variable] = "ws"
                if "Wind Direction" in variable:
                    cols_json[variable] = "wd"
                if "Site Outdoor Air Relative Humidity" in variable:
                    cols_json[variable] = "hr"
                if "Environment:Site Diffuse Solar Radiation Rate" in variable:
                    cols_json[variable] = "Id"
                if "Environment:Site Direct Solar Radiation Rate" in variable:
                    cols_json[variable] = "Ib"
            except:
                pass

    def get_data(self, names):
        result = [variable for name in names for variable in self.vars if name in variable]
        return self.data[result]

    def get_construction(self,names_cs,round=4):
#         all = []
        for name_cs in names_cs:
            properties = ['NameMaterial','Conductivity', 'Density','SpecHeat', 'Thickness', 
                          'TotalLayers', 'InsideAbsorpVis', 'OutsideAbsorpVis','InsideAbsorpSolar',
                          'OutsideAbsorpSolar', 'InsideAbsorpThermal',
                          'OutsideAbsorpThermal', 'OutsideRoughness']
            cs = self.mlc.loc[self.mlc.NameConstruction==name_cs].sort_values('ConstructionLayersIndex')[properties]
            thickness =  cs['Thickness'].sum().round(round)
            total_layers = cs.TotalLayers.unique()
            InsideAbsopVis = cs.InsideAbsorpVis.unique()
            OutsideAbsopVis = cs.OutsideAbsorpVis.unique()
            OutsideAbsorpSolar = cs.OutsideAbsorpSolar.unique()
            InsideAbsorpThermal = cs.InsideAbsorpThermal.unique()
            OutsideAbsorpThermal = cs.OutsideAbsorpThermal.unique()
            OutsideRoughness = cs.OutsideRoughness.unique()
            print('\n')
            print(f'Construction system:\033[1m{name_cs}\033[0m')
            print(f'Total thickness    :{thickness} m')
            print(f'Total layers:{total_layers}')
            print(f"InsideAbsorpVis:{InsideAbsopVis}")
            print(f"OutsideAbsorpVis:{OutsideAbsopVis}")
            print(f"OutsideAbsorpSolar:{OutsideAbsorpSolar}")
            print(f"InsideAbsorpThermal:{InsideAbsorpThermal}")
            print(f"OutsideRoughness:{OutsideRoughness}")
            properties = ['NameMaterial','Conductivity', 'Density','SpecHeat', 'Thickness']
            display(cs[properties])
            #print(cs[properties])
            print('\n\n\n')
        #return a1+a2+a3+a4+a5+a6+a7+a8+a9+a10
#         return all



def read_epw(file,year=None,alias=False,warns=True):
    """
    Read EPW file 
    
    Arguments:
    ----------
    file -- path location of EPW file
    year -- None default to leave intact the year or change if desired. It raises a warning.
    alias -- False default, True to change to To, Ig, Ib, Ws, RH, ...
    
    """
  
    names = ['Year',
               'Month',
               'Day',
               'Hour',
               'Minute',
               'Data Source and Uncertainty Flags',
               'Dry Bulb Temperature',
               'Dew Point Temperature',
               'Relative Humidity',
               'Atmospheric Station Pressure',
               'Extraterrestrial Horizontal Radiation',
               'Extraterrestrial Direct Normal Radiation',
               'Horizontal Infrared Radiation Intensity',
               'Global Horizontal Radiation',
               'Direct Normal Radiation',
               'Diffuse Horizontal Radiation',
               'Global Horizontal Illuminance',
               'Direct Normal Illuminance',
               'Diffuse Horizontal Illuminance',
               'Zenith Luminance',
               'Wind Direction',
               'Wind Speed',
               'Total Sky Cover',
               'Opaque Sky Cover',
               'Visibility',
               'Ceiling Height',
               'Present Weather Observation',
               'Present Weather Codes','Precipitable Water','Aerosol Optical Depth','Snow Depth','Days Since Last Snowfall',
               'Albedo','Liquid Precipitation Depth','Liquid Precipitation Quantity']
    
    rename = {'Dry Bulb Temperature'        :'To',
              'Relative Humidity'           :'RH',
              'Atmospheric Station Pressure':'P' ,
              'Global Horizontal Radiation' :'Ig',
              'Direct Normal Radiation'     :'Ib',
              'Diffuse Horizontal Radiation':'Id',
              'Wind Direction'              :'Wd',
              'Wind Speed'                  :'Ws'}
    data = pd.read_csv(file,skiprows=8,header=None,names=names,usecols=range(35))
#     data.Minute = 0
#     data.loc[data.Hour==24,['Hour','Minute']] = [23,59]
    data.Hour = data.Hour -1
    if year != None:
        data.Year = year
        if warns == True:
            warnings.warn("Year has been changed, be carefull")
    try:
        data['tiempo'] = data.Year.astype('str') + '-' + data.Month.astype('str')  + '-' + data.Day.astype('str') + ' ' + data.Hour.astype('str') + ':' + data.Minute.astype('str') 
        data.tiempo = pd.to_datetime(data.tiempo,format='%Y-%m-%d %H:%M')
    except:
        data.Minute = 0
        data['tiempo'] = data.Year.astype('str') + '-' + data.Month.astype('str')  + '-' + data.Day.astype('str') + ' ' + data.Hour.astype('str') + ':' + data.Minute.astype('str') 
        data.tiempo = pd.to_datetime(data.tiempo,format='%Y-%m-%d %H:%M')
        
    data.set_index('tiempo',inplace=True)
    del data['Year']
    del data['Month']
    del data['Day']
    del data['Hour']
    del data['Minute']
    if alias:
        data.rename(columns=rename,inplace=True)
    return data





def to_epw(file,df,epw_file):
    """
    Save dataframe to EPW 
    
    Arguments:
    ----------
    file -- path location of EPW file
    """
  
    
  
    names = ['Year',
               'Month',
               'Day',
               'Hour',
               'Minute',
               'Data Source and Uncertainty Flags',
               'Dry Bulb Temperature',
               'Dew Point Temperature',
               'Relative Humidity',
               'Atmospheric Station Pressure',
               'Extraterrestrial Horizontal Radiation',
               'Extraterrestrial Direct Normal Radiation',
               'Horizontal Infrared Radiation Intensity',
               'Global Horizontal Radiation',
               'Direct Normal Radiation',
               'Diffuse Horizontal Radiation',
               'Global Horizontal Illuminance',
               'Direct Normal Illuminance',
               'Diffuse Horizontal Illuminance',
               'Zenith Luminance',
               'Wind Direction',
               'Wind Speed',
               'Total Sky Cover',
               'Opaque Sky Cover',
               'Visibility',
               'Ceiling Height',
               'Present Weather Observation',
               'Present Weather Codes','Precipitable Water','Aerosol Optical Depth','Snow Depth','Days Since Last Snowfall',
               'Albedo','Liquid Precipitation Depth','Liquid Precipitation Quantity']
    
    
    rename = {'To':'Dry Bulb Temperature'        ,
              'RH':'Relative Humidity'           ,
              'P' :'Atmospheric Station Pressure',
              'Ig':'Global Horizontal Radiation' ,
              'Ib':'Direct Normal Radiation'     ,
              'Id':'Diffuse Horizontal Radiation',
              'Wd':'Wind Direction'              ,
              'Ws':'Wind Speed'                  }
    
    df2 = df.copy()
    df2.rename(columns=rename,inplace=True)
    df2['Year']    = df2.index.year
    df2['Month']   = df2.index.month
    df2['Day']     = df2.index.day
    df2['Hour']    = df2.index.hour
    df2['Minute']  = 60
    
    
    with open(epw_file) as myfile:
        head = [next(myfile) for x in range(8)]
    
    epw_header = ''
    for texto in head:
        epw_header += texto
        
    df2[names].to_csv(file,header=None,index=False)
    with open(file) as f:
        epw = f.read()
    
    epw_tail = ''
    for texto in epw:
        epw_tail += texto
    epw = epw_header + epw_tail
    
    
    with open(file, 'w') as f:
        f.write(epw)

