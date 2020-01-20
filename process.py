import numpy as np
import xarray as xr
import re
from math import ceil, sqrt

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
    experiments = ['simulations']
    floatPrecision = '{: 0.2f}'
    seedVars = ['Seed']
    timeSamples = 2000
    minTime = 0
    maxTime = 2000
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
    shouldRecompute = False#newestFileTime != lastTimeProcessed
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
    from mpl_toolkits.mplot3d import Axes3D # needed for 3d projection
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    figure_size=(6, 6)
    matplotlib.rcParams.update({'axes.titlesize': 13})
    matplotlib.rcParams.update({'axes.labelsize': 12})
    
    kcovColors = ['#00d0ebFF','#61a72cFF','#e30000FF']
    kcovEcolors = ['#0300ebFF', '#8cff9dFF', '#f5b342FF'] # error bars
    kcovVariables = ['1-coverage','2-coverage','3-coverage']
    kcovTrans = ['1-cov','2-cov','3-cov']
    algos = ['ff_linpro', 'zz_linpro','ff_linproF', 'zz_linproF', 'ff_nocomm', 'nocomm', 'sm_av', 'bc_re']#data.coords['Algorithm'].data.tolist()
    
    data = datasets['simulations']
    # now load data from previous simulations
    oldData = pickle.load(open('data_summary_datasets_20200106', 'rb'))['simulations']
    data = xr.combine_by_coords([data, oldData])
    
    dataMean = data.mean('time')
    dataKcovsMean = dataMean.mean('Seed')
    dataKcovsStd = dataMean.std('Seed')
    
    dataDist = data.sum('time').assign(MovEfficiency = lambda d: d.ObjDist / d.CamDist)
    dataDistMean = dataDist.mean('Seed')
    dataDistStd = dataDist.std('Seed')
    
    simRatios = data.coords['CamObjRatio'].data.tolist()
    simRatios.reverse()
    commRanges = data.coords['CommunicationRange'].data.tolist()
    commRanges.reverse()
    """""""""""""""""""""""""""
                kcov 3D
    """""""""""""""""""""""""""
    def getSurfData(dataarray, xcord, ycord):
        xs = []
        ys = []
        zs = []
        for xd in dataarray:
            for yd in xd:
                xs.append(xd[xcord].values.tolist())
                ys.append(yd[ycord].values.tolist())
                zs.append(yd.values.tolist())
        return xs, ys, zs
        
    fig = plt.figure(figsize=(12,20))
    for idx, algo in enumerate(algos):
        cols = 2
        rows = ceil(len(algos) / 2)
        ax = fig.add_subplot(rows,cols,idx+1, projection='3d')
        
        # Make data.
        #X = commRanges
        #Y = simRatios
        #X, Y = np.meshgrid(X, Y)

        ax.set_xlabel("CommRange")
        ax.set_ylabel("Cam/Obj")
        #if idx%cols == cols-1:
        ax.set_zlabel("Coverage (%)")
        #else:
        #    ax.set_zticklabels([])
        ax.set_xlim([max(commRanges),min(commRanges)])
        ax.set_ylim([min(simRatios),max(simRatios)])
        ax.set_zlim([0,1])
        ax.set_title(algo)
        
        fakeLinesForLegend = []
        def kcov(whichKCov,x,y):
            return dataKcovsMean[whichKCov].sel(Algorithm=algo, CamObjRatio=y, CommunicationRange=x).values.tolist()#[0]
        forKcovVars = [kcovVariables[0], kcovVariables[-1]]
        forKcovTrans = []
        for k, whichKCov in enumerate(kcovVariables):
            if not whichKCov in forKcovVars:
                continue
            #zs = np.array(kcov(whichKCov, commRanges, simRatios))
            #Z = zs.reshape(X.shape)
            
            x,y,z = getSurfData(dataKcovsMean[whichKCov].sel(Algorithm=algo), 'CommunicationRange', 'CamObjRatio')
            ax.plot_trisurf(x,y,z, linewidth=2, antialiased=False, shade=True, alpha=0.5, color=kcovColors[k])
            #ax.plot_surface(X, Y, Z, linewidth=2, rstride=2, cstride=2, antialiased=False, shade=True, alpha=0.5, color=kcovColors[k])
            #ax.plot_wireframe(X, Y, Z, linewidth=2, rstride=2, cstride=2, antialiased=False, color=kcovColors[k])
            fakeLinesForLegend.append(matplotlib.lines.Line2D([0],[0], linestyle='none', c=kcovColors[k], marker='o'))
            forKcovTrans.append(kcovTrans[k])
        """
        top1 = [min(commRanges), min(simRatios), 0]
        top2 = [max(commRanges), min(simRatios), 0]
        top3 = [max(commRanges), min(simRatios), kcov('1-coverage',max(commRanges), min(simRatios))]
        #top4 = [min(commRanges), min(simRatios), kcov(max(commRanges), max(simRatios))]
        vertices = [top1, top2, top3]
        for cr in commRanges:
            vertices.append([cr, min(simRatios), kcov('1-coverage',cr, min(simRatios))])
        print(algo)
        print(vertices)
        pols = Poly3DCollection([vertices])
        pols.set_facecolor(kcovColors[0])
        pols.set_edgecolor(kcovColors[0])
        ax.add_collection3d(pols)
        """
        if idx == cols-1:
            ax.legend(fakeLinesForLegend, forKcovTrans, numpoints=1)
        
    plt.tight_layout()
    fig.savefig(charts_dir + 'KCov_3D.pdf', bbox_inches = 'tight', pad_inches = 0)
    plt.close(fig)
    exit()
    
    """""""""""""""""""""""""""
        kcoverage comparison
    """""""""""""""""""""""""""
    for r,commRange in enumerate(commRanges):
        fig = plt.figure(figsize=(22,20))
        for j,simRatio in enumerate(simRatios):
            # rows, columns, index
            #size = ceil(sqrt(len(simRatios)))
            rows = 4#size-1
            cols = 5#size
            ax = fig.add_subplot(rows, cols,j+1)
            ax.set_ylim([0,1])
            #if j<size:
            ax.set_title("Cam/Obj Ratio = {0:.1f}".format(simRatio))
            if j%cols == 0:
                ax.set_ylabel("Coverage (%)")
            plt.xticks(rotation=35, ha='right')
            ax.yaxis.grid(True)

            for i,s in enumerate(kcovVariables):
                values = [dataKcovsMean[s].sel(Algorithm=algoname, CamObjRatio=simRatio, CommunicationRange=commRange).values.tolist() for algoname in algos]
                errors = [dataKcovsStd[s].sel(Algorithm=algoname, CamObjRatio=simRatio, CommunicationRange=commRange).values.tolist() for algoname in algos]
                ax.bar(algos, values, yerr=errors, label=kcovTrans[i], capsize=4, color=kcovColors[i], ecolor=kcovEcolors[i])
            if j == cols-1:
                ax.legend()
        plt.tight_layout()
        fig.savefig(charts_dir + 'KCov_CommRange-'+str(commRange)+'_CamObjRatio-variable.pdf')
        plt.close(fig)
    
    algosWithoutNocomm = algos#[a for a in algos if a != "nocomm"]
    for r,simRatio in enumerate(simRatios):
        fig = plt.figure(figsize=(14,10))
        for j,commRange in enumerate(commRanges):
            # rows, columns, index
            size = ceil(sqrt(len(commRanges)))
            rows = size-1
            cols = size
            ax = fig.add_subplot(rows, cols,j+1)
            ax.set_ylim([0,1])
            ax.set_title("Comm Range = {0:.0f}".format(commRange))
            if j%cols == 0:
                ax.set_ylabel("Coverage (%)")
            plt.xticks(rotation=35, ha='right')
            ax.yaxis.grid(True)

            for i,s in enumerate(kcovVariables):
                values = [dataKcovsMean[s].sel(Algorithm=algoname, CamObjRatio=simRatio, CommunicationRange=commRange).values.tolist() for algoname in algosWithoutNocomm]
                errors = [dataKcovsStd[s].sel(Algorithm=algoname, CamObjRatio=simRatio, CommunicationRange=commRange).values.tolist() for algoname in algosWithoutNocomm]
                ax.bar(algosWithoutNocomm, values, yerr=errors, label=kcovTrans[i], capsize=4, color=kcovColors[i], ecolor=kcovEcolors[i])
            if j == cols-1:
                ax.legend()
        plt.tight_layout()
        fig.savefig(charts_dir + 'KCov_CommRange-variable_CamObjRatio-'+str(simRatio)+'.pdf')
        plt.close(fig)
    
    """""""""""""""""""""""""""
        single algos kcov
    """""""""""""""""""""""""""
    
    simRatios.reverse()
    commRanges.reverse()
    for commRange in commRanges:
        fig = plt.figure(figsize=(18,8))
        for idx,algo in enumerate(algos):
            #size = ceil(sqrt(len(algos)))
            rows = 2
            cols = 4
            ax = fig.add_subplot(rows,cols,idx+1)
            ax.set_ylim([0,1])
            ax.set_xlim([min(simRatios) - 0.1, max(simRatios) + 0.1])
            if idx%cols == 0:
                ax.set_ylabel("Coverage (%)")
            if idx < cols:
                ax.set_xlabel("Cam/Obj Ratio")
            if idx%rows != 0:
                ax.set_yticklabels([])
            ax.set_title(algo)
            ax.set_xticks([0] + simRatios + [max(simRatios) + 0.1])
            ax.set_xticklabels([""] + simRatios + [""])
            #if idx < 6:
            #    ax.set_xticklabels([])
            chartdataMean = dataKcovsMean.sel(Algorithm=algo, CommunicationRange=commRange)
            chartdataStd = dataKcovsStd.sel(Algorithm=algo, CommunicationRange=commRange)
            #xax = np.linspace(min(simRatios),max(simRatios),len(simRatios))
            for i,s in enumerate(kcovVariables):
                values = chartdataMean[s].values.tolist()
                #values.reverse()
                errors = chartdataStd[s].values.tolist()
                #.reverse()
                ax.plot(simRatios, values, label=kcovTrans[i], color=kcovColors[i])
                for j,r in enumerate(simRatios):
                    ax.errorbar(r, values[j], yerr=errors[j], fmt='.', color=kcovEcolors[i], capsize=4)
            if idx == cols-1:
                ax.legend()
        plt.tight_layout()
        fig.savefig(charts_dir + 'KCov_lines_CommRange-'+str(commRange)+'_CamObjRatio-variable.pdf')
        plt.close(fig)
    
    
    for simRatio in simRatios:
        fig = plt.figure(figsize=(18,8))
        for idx,algo in enumerate(algos):
            #size = ceil(sqrt(len(algos)))
            rows = 2
            cols = 4
            ax = fig.add_subplot(rows,cols,idx+1)
            minRange = min(commRanges) - 10
            maxRange = max(commRanges) + 10
            ax.set_ylim([0,1])
            ax.set_xlim([minRange, maxRange])
            if idx%cols == 0:
                ax.set_ylabel("Coverage (%)")
            if idx < cols:
                ax.set_xlabel("CommRange")
            if idx%rows != 0:
                ax.set_yticklabels([])
            ax.set_title(algo)
            ax.set_xticks([minRange] + commRanges + [maxRange])
            ax.set_xticklabels([""] + [str(round(c)) for c in commRanges] + [""])
            chartdataMean = dataKcovsMean.sel(Algorithm=algo, CamObjRatio=simRatio)
            chartdataStd = dataKcovsStd.sel(Algorithm=algo, CamObjRatio=simRatio)
            for i,s in enumerate(kcovVariables):
                values = chartdataMean[s].values.tolist()
                errors = chartdataStd[s].values.tolist()
                ax.plot(commRanges, values, label=kcovTrans[i], color=kcovColors[i])
                for j,r in enumerate(commRanges):
                    ax.errorbar(r, values[j], yerr=errors[j], fmt='.', color=kcovEcolors[i], capsize=4)
            if idx == cols-1:
                ax.legend()
        plt.tight_layout()
        fig.savefig(charts_dir + 'KCov_lines_CommRange-variable_CamObjRatio-'+str(simRatio)+'.pdf')
        plt.close(fig)

    
    """""""""""""""""""""""""""
        distance traveled
    """""""""""""""""""""""""""
    chartDataMean = dataDistMean.sel(CamObjRatio=1)
    chartDataStd = dataDistStd.sel(CamObjRatio=1)
    
    simRatio = 1
    for r,commRange in enumerate(commRanges):
        fig = plt.figure(figsize=(6,6))
        ax = fig.add_subplot(1, 1, 1)
        ax.set_ylim([0,1])
        #if j<size:
        #ax.set_title("Cam/Obj Ratio = {0:.1f}".format(simRatio))
        if j%cols == 0:
            ax.set_ylabel("MovEfficiency (%)")
        plt.xticks(rotation=35, ha='right')
        ax.yaxis.grid(True)

        #for i,s in enumerate(kcovVariables):
        values = [chartDataMean.MovEfficiency.sel(Algorithm=algoname, CommunicationRange=commRange).values.tolist() for algoname in algos]
        errors = [chartDataStd.MovEfficiency.sel(Algorithm=algoname, CommunicationRange=commRange).values.tolist() for algoname in algos]
        ax.bar(algos, values, yerr=errors, capsize=4, color=kcovColors[i], ecolor=kcovEcolors[i])

        plt.tight_layout()
        fig.savefig(charts_dir + 'MovEfficiency_CamObjRatio-'+str(simRatio)+'_CommRange-'+str(commRange)+'.pdf')
        plt.close(fig)
    
    
    
    
    
    
        