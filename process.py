import numpy as np
import xarray as xr
import re

def distance(val, ref):
    return abs(ref - val)
vectDistance = np.vectorize(distance)

def getClosest(sortedMatrix, column, val):
    while len(sortedMatrix) > 3:
        half = int(len(sortedMatrix) / 2)
        sortedMatrix = sortedMatrix[-half - 1:] if sortedMatrix[half, column] < val else sortedMatrix[: half + 1]
    if len(sortedMatrix) == 1:
        result = sortedMatrix[0].copy()
        result[column] = val
        return result
    else:
        safecopy = sortedMatrix.copy()
        safecopy[:, column] = vectDistance(safecopy[:, column], val)
        minidx = np.argmin(safecopy[:, column])
        safecopy = safecopy[minidx, :].A1
        safecopy[column] = val
        return safecopy

def convert(column, samples, matrix):
    return np.matrix([getClosest(matrix, column, t) for t in samples])

def valueOrEmptySet(k, d):
    return (d[k] if isinstance(d[k], set) else {d[k]}) if k in d else set()

def mergeDicts(d1, d2):
    """
    Creates a new dictionary whose keys are the union of the keys of two
    dictionaries, and whose values are the union of values.

    Parameters
    ----------
    d1: dict
        dictionary whose values are sets
    d2: dict
        dictionary whose values are sets

    Returns
    -------
    dict
        A dict whose keys are the union of the keys of two dictionaries,
    and whose values are the union of values

    """
    res = {}
    for k in d1.keys() | d2.keys():
        res[k] = valueOrEmptySet(k, d1) | valueOrEmptySet(k, d2)
    return res

def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False

def extractCoordinates(filename):
    """
    Scans the header of an Alchemist file in search of the variables.

    Parameters
    ----------
    filename : str
        path to the target file
    mergewith : dict
        a dictionary whose dimensions will be merged with the returned one

    Returns
    -------
    dict
        A dictionary whose keys are strings (coordinate name) and values are
        lists (set of variable values)

    """
    with open(filename, 'r') as file:
        regex = re.compile(' (?P<varName>[a-zA-Z]+) = (?P<varValue>(?:[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)|[a-zA-Z-_]*)?')
        dataBegin = re.compile('\d')
        for line in file:
            match = regex.findall(line)
            if match:
                return {var : (float(value) if is_float(value) else value) for var, value in match}
            elif dataBegin.match(line[0]):
                return {}

def extractVariableNames(filename):
    """
    Gets the variable names from the Alchemist data files header.

    Parameters
    ----------
    filename : str
        path to the target file

    Returns
    -------
    list of list
        A matrix with the values of the csv file

    """
    with open(filename, 'r') as file:
        dataBegin = re.compile('\d')
        lastHeaderLine = ''
        for line in file:
            if dataBegin.match(line[0]):
                break
            else:
                lastHeaderLine = line
        if lastHeaderLine:
            regex = re.compile(' (?P<varName>\S+)')
            return regex.findall(lastHeaderLine)
        return []

def openCsv(path):
    """
    Converts an Alchemist export file into a list of lists representing the matrix of values.

    Parameters
    ----------
    path : str
        path to the target file

    Returns
    -------
    list of list
        A matrix with the values of the csv file

    """
    regex = re.compile('\d')
    with open(path, 'r') as file:
        lines = filter(lambda x: regex.match(x[0]), file.readlines())
        return [[float(x) for x in line.split()] for line in lines]

if __name__ == '__main__':
    # CONFIGURE SCRIPT
    directory = 'data'
    pickleOutput = 'data_summary'
    experiments = ['fully_connected']
    floatPrecision = '{: 0.2f}'
    seedVars = ['Seed']
    timeSamples = 2000
    minTime = 0
    maxTime = 2000.1
    timeColumnName = 'time'
    logarithmicTime = False
    
    # Setup libraries
    np.set_printoptions(formatter={'float': floatPrecision.format})
    # Read the last time the data was processed, reprocess only if new data exists, otherwise just load
    import pickle
    import os
    newestFileTime = max(os.path.getmtime(directory + '/' + file) for file in os.listdir(directory))
    try:
        lastTimeProcessed = pickle.load(open('timeprocessed', 'rb'))
    except:
        lastTimeProcessed = -1
    shouldRecompute = newestFileTime != lastTimeProcessed
    datasets = dict()
    if not shouldRecompute:
        try:
            #means = pickle.load(open(pickleOutput + '_mean', 'rb'))
            #stdevs = pickle.load(open(pickleOutput + '_std', 'rb'))
            datasets = pickle.load(open(pickleOutput + '_datasets', 'rb'))
        except:
            shouldRecompute = True
            
    if shouldRecompute:
        timefun = np.logspace if logarithmicTime else np.linspace
        means = {}
        stdevs = {}
        for experiment in experiments:
            # Collect all files for the experiment of interest
            import fnmatch
            allfiles = filter(lambda file: fnmatch.fnmatch(file, experiment + '_*.txt'), os.listdir(directory))
            allfiles = [directory + '/' + name for name in allfiles]
            allfiles.sort()
            # From the file name, extract the independent variables
            dimensions = {}
            for file in allfiles:
                dimensions = mergeDicts(dimensions, extractCoordinates(file))
            dimensions = {k: sorted(v) for k, v in dimensions.items()}
            # Add time to the independent variables
            dimensions[timeColumnName] = range(0, timeSamples)
            # Compute the matrix shape
            shape = tuple(len(v) for k, v in dimensions.items())
            # Prepare the Dataset
            dataset = xr.Dataset()
            for k, v in dimensions.items():
                dataset.coords[k] = v
            varNames = extractVariableNames(allfiles[0])
            for v in varNames:
                if v != timeColumnName:
                    novals = np.ndarray(shape)
                    novals.fill(float('nan'))
                    dataset[v] = (dimensions.keys(), novals)
            # Compute maximum and minimum time, create the resample
            timeColumn = varNames.index(timeColumnName)
            allData = { file: np.matrix(openCsv(file)) for file in allfiles }
            computeMin = minTime is None
            computeMax = maxTime is None
            if computeMax:
                maxTime = float('-inf')
                for data in allData.values():
                    maxTime = max(maxTime, data[-1, timeColumn])
            if computeMin:
                minTime = float('inf')
                for data in allData.values():
                    minTime = min(minTime, data[0, timeColumn])
            #print(allData)
            timeline = timefun(minTime, maxTime, timeSamples)
            # Resample
            for file in allData:
                allData[file] = convert(timeColumn, timeline, allData[file])
                
            # Populate the dataset
            for file, data in allData.items():
                dataset[timeColumnName] = timeline
                for idx, v in enumerate(varNames):
                    if v != timeColumnName:
                        darray = dataset[v]
                        experimentVars = extractCoordinates(file)
                        darray.loc[experimentVars] = data[:, idx].A1
            #print(dataset)
            # Fold the dataset along the seed variables, producing the mean and stdev datasets
            #means[experiment] = dataset.mean(seedVars)
            #stdevs[experiment] = dataset.std(seedVars)
            datasets[experiment] = dataset
        # Save the datasets
        #pickle.dump(means, open(pickleOutput + '_mean', 'wb'), protocol=-1)
        #pickle.dump(stdevs, open(pickleOutput + '_std', 'wb'), protocol=-1)
        pickle.dump(datasets, open(pickleOutput + '_datasets', 'wb'), protocol=-1)
        pickle.dump(newestFileTime, open('timeprocessed', 'wb'))

    # Prepare the charting system
    import matplotlib
    import matplotlib.pyplot as plt
    import matplotlib.cm as cmx
    figure_size=(6, 6)
    matplotlib.rcParams.update({'axes.titlesize': 14})
    matplotlib.rcParams.update({'axes.labelsize': 13})
    
    kcovColors = ['#00d0ebFF','#61a72cFF','#e30000FF']
    kcovEcolors = ['#0300ebFF', '#8cff9dFF', '#f5b342FF'] # error bars
    kcovVariables = ['1-coverage','2-coverage','3-coverage']
    algos = ['ff_linpro', 'zz_linpro', 'ff_nocomm', 'nocomm', 'sm_av', 'bc_re']#data.coords['Algorithm'].data.tolist()
    
    data = datasets['fully_connected']
    dataFullyMean = data.mean('time')
    dataFullyKcovsMean = dataFullyMean.mean('Seed')
    dataFullyKcovsStd = dataFullyMean.std('Seed')
    simRatios = data.coords['HumansCamerasRatio'].data.tolist()
    simRatios.reverse()
    """""""""""""""""""""""""""
        kcoverage comparison
    """""""""""""""""""""""""""
    
    fig = plt.figure(figsize=figure_size)
    
    for j,simRatio in enumerate(simRatios):
        # rows, columns, index
        ax = fig.add_subplot(2,2,j+1)
        ax.set_ylim([0,1])
        ax.set_title("C/T Ratio = {0:.1f}".format(simRatio))
        if j%2 == 0:
            ax.set_ylabel("Coverage (%)")
        plt.xticks(rotation=35, ha='right')
        ax.yaxis.grid(True)

        for i,s in enumerate(kcovVariables):
            values = [dataFullyKcovsMean[s].sel(Algorithm=algoname, HumansCamerasRatio=simRatio).values.tolist() for algoname in algos]
            errors = [dataFullyKcovsStd[s].sel(Algorithm=algoname, HumansCamerasRatio=simRatio).values.tolist() for algoname in algos]
            ax.bar(algos, values, yerr=errors, label=s, capsize=4, color=kcovColors[i], ecolor=kcovEcolors[i])
        if j == 1:
            ax.legend()

    
    plt.tight_layout()
    fig.savefig('kcov_comparison.pdf')
    
    """""""""""""""""""""""""""
        single algos
    """""""""""""""""""""""""""
    
    for algo in algos:
        fig = plt.figure(figsize=figure_size)
        ax = fig.add_subplot(1,1,1)
        ax.set_ylim([0,1])
        ax.set_xlim([max(simRatios) + 0.1, min(simRatios) - 0.1])
        ax.set_ylabel("Coverage (%)")
        ax.set_xlabel("C/T Ratio")
        ax.set_title(algo)
        ax.set_xticks([1.1] + simRatios + [0])
        ax.set_xticklabels([""] + simRatios + [""])
        chartdataMean = dataFullyKcovsMean.sel(Algorithm=algo)
        chartdataStd = dataFullyKcovsStd.sel(Algorithm=algo)
        #xax = np.linspace(min(simRatios),max(simRatios),len(simRatios))
        for i,s in enumerate(kcovVariables):
            values = chartdataMean[s].values.tolist()
            values.reverse()
            errors = chartdataStd[s].values.tolist()
            errors.reverse()
            ax.plot(simRatios, values, label=s, color=kcovColors[i])
            for j,r in enumerate(simRatios):
                ax.errorbar(r, values[j], yerr=errors[j], fmt='o', color=kcovEcolors[i], capsize=4)
        ax.legend()
        plt.tight_layout()
        fig.savefig(algo+'.pdf')
    exit()
    
    
    data = dataset
    print("DATASET")
    print(dataset)
    print("")
    print("")
    print("DATASET SEL SMAV")
    print(dataset.sel(Algorithm='smav'))
    print("")
    print("")
    print("DATASET SEL SMAV MEAN SEED")
    print(dataset.sel(Algorithm='smav').mean())
    print(dataset.sel(Algorithm='smav').std())
    print("")
    print("")
    print("DATASET SEL SMAV MEAN SEED")
    print(dataset.sel(Algorithm='simplex').mean('time').mean())
    print(dataset.sel(Algorithm='smav').mean('time').mean())
    print(dataset.sel(Algorithm='simplex').sum('time').mean())
    print(dataset.sel(Algorithm='smav').sum('time').mean())
    #print(dataset.sel(Algorithm='simplex').mean('time').mean())
    #print(dataset.sel(Algorithm='simplex').mean('time').std())
    #print(dataset.sel(Algorithm='smav').mean('time').mean())
    #print(dataset.sel(Algorithm='smav').mean('time').std())
    #print("")
    #print("")
    #print("MEANS SEL MEAN")
    exit()
    
    fig = plt.figure(figsize=figure_size)
    plt.ylim(0, 1)
    ax = fig.add_subplot(1,1,1)
    ax.yaxis.grid(True)

    algos = data.coords['Algorithm'].data.tolist()
    series = ['1-coverage','2-coverage','3-coverage']
    for s in series:
        cov = [data[s].sel(Algorithm=algoname).mean(seedVars).values.tolist() for algoname in algos]
        covyerr = [data[s].sel(Algorithm=algoname).std(seedVars).values.tolist() for algoname in algos]

        ax.bar(algos, cov, yerr=covyerr, label=s, capsize=5)

    #ax.xticks(algos)
    #ax.ylabel("Medals")
    #ax.xlabel("Countries")
    ax.legend(loc="upper right")
    #ax.title("2012 Olympics Top Scorers")
    fig.savefig('kcov.pdf')
    """
    print("means")
    print(data)
    varMeanings = {
        "1-coverage" : "Number of targets covered by 1 camera",
        "2-coverage" : "Number of targets covered by 2 cameras",
        "3-coverage" : "Number of targets covered by 3 cameras",
        "distance" : "Distance traveled (m)"
    }
    for var in data.data_vars:
        chartsetdata = data[var]
        xdata = chartsetdata['time'] / 60
        reifiedcoords = [x for x in chartsetdata.coords if x != 'time']
        for coord in reifiedcoords:
            fig = plt.figure(figsize = figure_size)
            ax = fig.add_subplot(1, 1, 1)
            ax.set_xlabel("Simulated time (minutes)")
            ax.set_xlim(min(xdata), max(xdata))
            ax.set_title(coord)
            ax.set_ylabel(varMeanings[chartsetdata.name])
#            ax.set_yscale('log')
            mergedata = chartsetdata.mean([x for x in reifiedcoords if x != coord])
            for linename in mergedata[coord]:
                chartdata = mergedata.loc[{coord: linename.values}]
                ax.plot(xdata, chartdata, label = str(linename.values))
            ax.legend()
    """
    
    
    
    # Prepare selected charts
    # Evaluation of the backoff parameter
    """
    def makechart(title, ylabel, ydata, colors = None):
        fig = plt.figure(figsize = figure_size)
        ax = fig.add_subplot(1, 1, 1)
        ax.set_title(title)
        xdata = means['simulation']['time'] / 60
        ax.set_xlabel("Simulated time (minutes)")
        ax.set_ylabel(ylabel)
#        ax.set_ylim(0)
        ax.set_xlim(min(xdata), max(xdata))
        plt.axvline(x=10, color='black', linestyle='dashed')
        index = 0
        for (label, data) in ydata.items():
            ax.plot(xdata, data.sel(Algorithm='simplex'), label=label, color=colors(index / (len(ydata) - 1)) if colors else None)
            index += 1
        return (fig, ax)
    print(data)
    chartdata = data['1-coverage'].mean()
    print(chartdata)
    (fig, ax) = makechart(
        "K-Coverage",
        '% coverage',
        {
            "1-coverage": data['1-coverage'],
            "2-coverage": data['2-coverage'],
            "3-coverage": data['3-coverage']
        },
#        colors = cmx.jet
    )
    ax.legend(ncol = 2)
    fig.savefig('simplex.pdf')
    """

    
    """
    chartdata = data['sourceLevel[Mean]'].mean(['shutdownProbability', 'peoplecount'])
    (fig, ax) = makechart(
        "K-Coverage",
        varMeanings['sourceLevel[Mean]'],
        {
            "disabled": chartdata[0],
            "Î±=0.001": chartdata[2],
            "Î±=0.01": chartdata[3],
            "Î±=0.1": chartdata[4],
            "Î±=1": chartdata[5],
            "Î±=0": chartdata[1],
        },
#        colors = cmx.jet
    )
    ax.legend(ncol = 2)
    fig.savefig('feedbackalpha0.pdf')

    chartdata = data['sourceLevel[StandardDeviation]'].mean(['shutdownProbability', 'peoplecount'])
    (fig, ax) = makechart(
        "Evaluation of the feedback loop for varying Î±",
        varMeanings['sourceLevel[StandardDeviation]'],
        {
            "disabled": chartdata[0],
            "Î±=0.001": chartdata[2],
            "Î±=0.01": chartdata[3],
            "Î±=0.1": chartdata[4],
            "Î±=1": chartdata[5],
            "Î±=0": chartdata[1],
        }
    )
    ax.set_ylim(0, 160)
    ax.legend(ncol = 3)
    fig.savefig('feedbackalpha1.pdf')
    mixcolormap = lambda x: cmx.winter(1 - x * 2) if x < 0.5 else cmx.YlOrRd((x - 0.5) * 2 * 0.7 + 0.3) # cmx.winter(1 - (x - 0.5) * 2)
    from string import Template
    for aggregator in ['Mean', 'StandardDeviation', 'Sum']:
        varname = 'sgcg[' + aggregator + ']'
        nofeedback = data[varname].sel(shutdownProbability=1, backoffAlpha=-1)
        feedback = data[varname].sel(shutdownProbability=1, backoffAlpha=0.01)
        template = Template('fb ${status} ${users} u')
        chartentries = {
            template.substitute(status = status, users = str(int(users))) : 
                (feedback if (status == 'on') else nofeedback).sel(peoplecount=users) 
            for status in ['on', 'off'] for users in feedback['peoplecount'] }
        (fig, ax) = makechart(
            "System performance with active users (Ï=1)",
            varMeanings[varname],
            chartentries,
            colors = mixcolormap
        )
        ax.set_yscale('log')
        ax.set_ylim(ax.get_ylim()[0] * 0.2)
        ax.legend(ncol = 3)
        fig.savefig(aggregator + "Performance.pdf")

        chartdata = data[varname].sel(peoplecount=500)
        template = Template('fb ${status} Ï=${rho}')
        chartentries = {
            template.substitute(status = status, rho = str(rho)) : 
                chartdata.sel(shutdownProbability=rho, backoffAlpha= 0.01 if status == 'on' else -1)
            for status in ['on', 'off'] for rho in chartdata['shutdownProbability'].values
        }
        (fig, ax) = makechart(
            "System resilience to disruption (500 users)",
            varMeanings[varname],
            chartentries,
            colors = mixcolormap
        )
        ax.set_ylim(ax.get_ylim()[0] * 0.2)
        ax.legend(ncol=3)
        fig.savefig(aggregator+"Resilience.pdf")
    """
        
        