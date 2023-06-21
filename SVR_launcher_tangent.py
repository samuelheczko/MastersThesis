
import glob
import os
import connectome
import nibabel as nib
import pandas as pd
import regresson

import sys; sys.path
import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt
import seaborn as sns
import time
from sklearn.preprocessing import normalize
from scipy.stats import uniform


from sklearn.metrics import explained_variance_score, r2_score
from sklearn.linear_model import Ridge

#from snapml import LinearRegression
from sklearn.utils.fixes import loguniform
from sklearn.svm import SVR




from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score, KFold

cluster = True
if cluster:
    path = '/home/sheczko/ptmp/data/' #global path for cluster
else:
    path = 'data/' ##local path for local computations

CT = 'tangent' #set the correlation type

Feature_selection = True ##set the wheter to use the feature selection trick based on the education scores



csv_paths  = glob.glob(path + f'/results/connectomes/{CT}_relevant/*.csv')
print(csv_paths)



##let's find the paths to the the csv connectivity data we ahve
#data_paths = glob.glob(path + '/results/connectomes/*tangent*.csv')

##load up regresors
regressors_df =  regresson.load_regressors(path + 'func_images/AOMIC/regressors/*.txt')
print(regressors_df.head())
##choose the target variables, take as np arrays
GCA = regressors_df.regressor_iq.values
bmi = regressors_df.regressor_bmi.values
edu = regressors_df.regressor_edu.values


 #concatenate cognitive metrics into single variable
cognition = ['GCA']
#cognition = ['PMAT Correct', 'PMAT Response Time']
cog_metric = np.transpose(np.asarray([GCA, edu]))

#set the number of permutations you want to perform
perm = 50
#set the number of cross-validation loops you want to perform
cv_loops = 5
#set the number of folds you want in the inner and outer folds of the nested cross-validation
k = 3
#set the proportion of data you want in your training set
train_size = .8
#set the number of variable you want to predict to be the number of variables stored in the cognition variablse
n_cog = np.size(cognition)
#set regression model type

#regr = Ridge(fit_intercept = True, max_iter=1000000) ##RIDGE
regr = SVR(kernel = 'rbf', max_iter=10000) ##SVR
params_dist = {'C' : loguniform(0.1 ,10e5),
                'epsilon': loguniform(0.01, 10)
                }

n_iter = 100 ## amount of iterations done to find the parameters
 


#regr = LinearRegression(fit_intercept = True, use_gpu=False, max_iter=1000000,dual=True,penalty='l2')
#set y to be the cognitive metrics you want to predict. They are the same for every atlas (each subject has behavioural score regradless of parcellation)
Y = cog_metric


column_names_pred = []
column_names_real = []

for perm_ixd in range(perm):
        for cog in cognition:
            column_names_pred.append(f'{cog}_perm_{perm_ixd + 1}_pred')
            column_names_real.append(f'{cog}_perm_{perm_ixd + 1}_real')

for n_feat in np.array([100,500,1000]):

    for data_path_i, data_path in enumerate(csv_paths): ##loop over atlases
            
        current_path = data_path
        #current_path = csv_paths[4]
        current_atlas = current_path.split('/')[-1].split('_')[-1].split('.')[0] #take the atlas name
        print(f'current ' + current_atlas)

        if current_atlas in ('atlas-Schaefer1000','atlas-Slab1068'):

            print('BIG skip in this atlas')
            continue

        fc = regresson.load_data(current_path) ##set the imput variable to the current atlas connectome, gives subjects x features matrix

        #set x data to be the input variable you want to use (we use always fc)
        
        X = fc
        X[X<0] = 0 #filter the negative values from the correlations
        #set the number of features 
        if Feature_selection:
            n_feat = n_feat
        else:
            n_feat = X.shape[1]


        #set hyperparameter grid space you want to search through for the model
        #alphas = np.linspace(max(n_feat*0.12 - 1000, 0.0001), n_feat*0.12 + 2000, num = 50, endpoint=True, dtype=None, axis=0) #set the range of alpahs being searhced based off the the amount of features



        r2, preds, var, corr, cogtest,opt_parameters,n_pred = regresson.regressionSVR(X = X, Y = Y, perm = perm, cv_loops = cv_loops, k = k, train_size = 0.8, n_cog = n_cog, regr = regr, params = params_dist,n_feat = n_feat,cognition = cognition, n_iter_search=n_iter,Feature_selection = True)
        
        ##save data:

        print(f'prediction: {corr,var}')

        df_preds = pd.DataFrame(preds.reshape(perm * n_cog,n_pred).T,columns = column_names_pred) ## we flatten the permutation axis 
        df_real = pd.DataFrame(cogtest.reshape(perm * n_cog,n_pred).T,columns = column_names_real)
        preds_real_df = pd.concat([df_preds,df_real],axis = 1, sort = True)


        result_r2 = pd.DataFrame(columns = [cog + '_r2' for cog in cognition], data = r2)
        result_var = pd.DataFrame(columns = [cog + '_var' for cog in cognition], data = var)
        opt_cs_df = pd.DataFrame(columns = [cog + '_opt_cs' for cog in cognition], data =  opt_parameters[:,:,0])
        opt_epsilons_df = pd.DataFrame(columns = [cog + '_opt_epsilons' for cog in cognition], data =  opt_parameters[:,:,1])

        corr_df = pd.DataFrame(columns = [cog + '_corr' for cog in cognition], data =  corr)

        result_df = pd.concat([result_var,result_r2,opt_cs_df,opt_epsilons_df,corr_df],axis = 1)

        if Feature_selection:
            result_df.to_csv(path + f'results/SV_regression/{CT}/SVM_results_FStd_n_feat_{n_feat}_rbf_scaled_cor_{CT}_{current_atlas}.csv')
            preds_real_df.to_csv(path + f'results/SV_regression/{CT}/SVM_preds_FStd_n_feat_{n_feat} rbf_scaled_cor_{CT}_{current_atlas}.csv')
        else:
            result_df.to_csv(path + f'results/SV_regression/{CT}/SVM_results_cor_{CT}_{current_atlas}.csv')
            preds_real_df.to_csv(path + f'results/SV_regression/{CT}/SVM_preds_cor_{CT}_{current_atlas}.csv')