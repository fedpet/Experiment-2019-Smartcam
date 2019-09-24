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
    charts_dir = 'charts/'
    pickleOutput = 'data_summary'
    experiments = ['fully_connected', 'limited_connection_range']
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
    matplotlib.rcParams.update({'axes.titlesize': 13})
    matplotlib.rcParams.update({'axes.labelsize': 12})
    
    kcovColors = ['#00d0ebFF','#61a72cFF','#e30000FF']
    kcovEcolors = ['#0300ebFF', '#8cff9dFF', '#f5b342FF'] # error bars
    kcovVariables = ['1-coverage','2-coverage','3-coverage']
    algos = ['ff_linpro', 'zz_linpro', 'ff_nocomm', 'nocomm', 'sm_av', 'bc_re']#data.coords['Algorithm'].data.tolist()
    
    dataFully = datasets['fully_connected']
    dataFullyMean = dataFully.mean('time')
    dataFullyKcovsMean = dataFullyMean.mean('Seed')
    dataFullyKcovsStd = dataFullyMean.std('Seed')
    
    dataLim = datasets['limited_connection_range']
    #print(dataLim)
    dataLimMean = dataLim.mean('time')
    dataLimKcovsMean = dataLimMean.mean('Seed')
    dataLimKcovsStd = dataLimMean.std('Seed')
    
    simRatios = dataFully.coords['HumansCamerasRatio'].data.tolist()
    simRatios.reverse()
    commRanges = dataLim.coords['ConnectionRange'].data.tolist()
    commRanges.reverse()
    commRanges = [c for c in commRanges if c != 25] # not ready yet
    """""""""""""""""""""""""""
        kcoverage comparison
    """""""""""""""""""""""""""
    fig = plt.figure(figsize=figure_size)
    
    for j,simRatio in enumerate(simRatios):
        # rows, columns, index
        ax = fig.add_subplot(2,2,j+1)
        ax.set_ylim([0,1])
        ax.set_title("Cam/Obj Ratio = {0:.1f}".format(simRatio))
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
    fig.savefig(charts_dir + 'fc_kcov_comparison.pdf')
    fig = plt.figure(figsize=figure_size)
    
    algosWithoutNocomm = algos#[a for a in algos if a != "nocomm"]
    for j,commRange in enumerate(commRanges):
        # rows, columns, index
        ax = fig.add_subplot(2,2,j+1)
        ax.set_ylim([0,1])
        ax.set_title("Comm Range = {0:.0f}".format(commRange))
        if j%2 == 0:
            ax.set_ylabel("Coverage (%)")
        plt.xticks(rotation=35, ha='right')
        ax.yaxis.grid(True)

        for i,s in enumerate(kcovVariables):
            values = [dataLimKcovsMean[s].sel(Algorithm=algoname, ConnectionRange=commRange).values.tolist() for algoname in algosWithoutNocomm]
            errors = [dataLimKcovsStd[s].sel(Algorithm=algoname, ConnectionRange=commRange).values.tolist() for algoname in algosWithoutNocomm]
            ax.bar(algosWithoutNocomm, values, yerr=errors, label=s, capsize=4, color=kcovColors[i], ecolor=kcovEcolors[i])
        if j == 1:
            ax.legend()
    plt.tight_layout()
    fig.savefig(charts_dir + 'lc_kcov_comparison.pdf')
    fig = plt.figure(figsize=figure_size)
    
    """""""""""""""""""""""""""
        single algos kcov
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
        fig.savefig(charts_dir + algo+'.pdf')
    
    """""""""""""""""""""""""""""""""
        limited connection range
    """""""""""""""""""""""""""""""""

        
        