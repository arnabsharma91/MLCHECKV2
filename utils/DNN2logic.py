#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import torch
import torchvision
import numpy as np
from torchvision import transforms, datasets
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import pandas as pd
import csv as cv
from joblib import load
from ast import literal_eval


class ConvertDNN2logic:
    
    def __init__(self, image_data=False):
        with open('param_dict.csv') as csv_file:
            reader = cv.reader(csv_file)
            self.paramDict = dict(reader) 
        if self.paramDict['multi_label'] == 'True':
            self.dnn = torch.load('Model/dnn_model_multi') 
        else:
            self.dnn = torch.load('Model/dnn_model')
        self.df = pd.read_csv('OracleData.csv')
        self.no_of_params = int(self.paramDict['no_of_params'])    
        self.no_of_hidden_layer = int(self.paramDict['no_of_layers'])
        self.no_of_layer = len(self.dnn.linears)
        self.no_of_class = self.dnn.linears[len(self.dnn.linears)-1].out_features
        self.image_data = image_data
        
    def remove_exponent(self, value):
        if 'e-' in value:
            decial = value.split('e')
            ret_val = format(((float(decial[0]))*(10**int(decial[1]))), '.5f')
            return ret_val
        else: 
            return value

    def funcDNN2logic(self):
        with open('feNameType.csv') as csv_file:
            reader = cv.reader(csv_file)
            feName_type = dict(reader)
        f=open('DNNSmt.smt2', 'w')
        f.write(';Input layer neurons \n')
        for i in range(0, self.no_of_params):
            f.write(';-----------'+str(i)+'th parameter----------------- \n')
            #Initializing input features
            for j in range(0, self.dnn.linears[0].in_features):
                if(self.image_data == False):
                    f.write('(declare-fun '+self.df.columns.values[j]+str(i)+' ()')
                    if('int' in str(self.df.dtypes[j])):
                        f.write(' Int) \n')
                    else:
                        f.write(' Real) \n')
                    f.write('(assert (and (>= '+self.df.columns.values[j]+str(i)+' 0) (<= '+self.df.columns.values[j]+str(i)
                    +' 1))) \n')
                else:
                    f.write('(declare-fun pixel'+str(j)+str(i)+' () Real) \n')
                            
            #Initializing hidden layer neurons
            for j in range(0, self.no_of_layer-1):
                for k in range(0, self.dnn.linears[j].out_features):
                    f.write('(declare-fun nron'+str(j)+str(k)+str(i)+' () Real) \n')
                    f.write('(declare-fun tmp'+str(j)+str(k)+str(i)+' () Real) \n')
            #Initializing output neurons
            for j in range(0, self.no_of_class):
                f.write('(declare-fun y'+str(j)+str(i)+' () Real) \n')
                f.write('(declare-fun tmp'+str(self.no_of_layer-1)+str(j)+str(i)+' () Real) \n')
            #Initializing extra variables needed for encoding argmax 
            for j in range(0, self.no_of_class):
                for k in range(0, self.no_of_class):
                    f.write('(declare-fun d'+str(j)+str(k)+str(i)+' () Int) \n')
            
            if(self.paramDict['multi_label'] == 'False'):
                if self.paramDict['regression'] == 'no':
                    f.write('(declare-fun Class'+str(i)+' () Int) \n')
                else:
                    f.write('(declare-fun Class' + str(i) + ' () Real) \n')
                    f.write('(assert (and (>= Class'+str(i)+' 0) (<= Class'+str(i)+' 1))) \n')

            else:
                for j in range(0, self.no_of_class):
                    class_name = self.df.columns.values[self.df.shape[1]-self.no_of_class+j]
                    f.write('(declare-fun '+class_name+str(i)+' () Int) \n')
                    f.write('(assert (and (>= '+class_name+str(i)+' 0) (<= '+class_name+str(i)+' 1))) \n')
    
        f.write('(define-fun absoluteInt ((x Int)) Int \n')
        f.write('  (ite (>= x 0) x (- x))) \n')
        f.write('(define-fun absoluteReal ((x Real)) Real \n')
        f.write('  (ite (>= x 0) x (- x))) \n')  

        for i in range(0, self.no_of_params):
            f.write(';-----------'+str(i)+'th parameter----------------- \n')
            f.write('\n ;Encoding the hidden layer neuron \n')
            for j in range(0, self.no_of_layer-1):
                for k in range(0, self.dnn.linears[j].out_features):
                    f.write('(assert (= ')
                    f.write('tmp'+str(j)+str(k)+str(i)+' (+')
                    if(j == 0):
                        for l in range(0, self.dnn.linears[j].in_features):
                            #temp_val = round(float(self.dnn.linears[j].weight[k][l]), 5)
                            temp_val = format(self.dnn.linears[j].weight[k][l], '.5f')
                            #print('temp_val before',temp_val)
                            if('e' in str(temp_val)):
                                temp_val = self.remove_exponent(str(temp_val))
                            #print('temp_val after',temp_val)    
                            if(self.image_data == False):
                                f.write('(* '+self.df.columns.values[l]+str(i)+' '+str(temp_val)+') ')
                            else:
                                f.write('(* pixel'+str(l)+str(i)+' '+str(temp_val)+') \n')
                        #temp_bias = round(float(self.dnn.linears[j].bias[k]), 5)
                        temp_bias = format(self.dnn.linears[j].bias[k], '.5f')
                        if('e' in str(temp_bias)):
                            temp_bias = self.remove_exponent(str(temp_bias))
                        f.write(str(temp_bias)+'))) \n')
                    else:
                        for l in range(0, self.dnn.linears[j].in_features):
                            #temp_val = round(float(self.dnn.linears[j].weight[k][l]), 5)
                            temp_val = format(self.dnn.linears[j].weight[k][l], '.5f')
                            if('e' in str(temp_val)):
                                temp_val = self.remove_exponent(str(temp_val))
                            f.write('(* nron'+str(j-1)+str(l)+str(i)+' '+str(temp_val)+')')
                        #temp_bias = round(float(self.dnn.linears[j].bias[k]), 5)
                        temp_bias = format(self.dnn.linears[j].bias[k], '.5f')
                        if('e' in str(temp_bias)):
                            temp_bias = self.remove_exponent(str(temp_bias))
                        f.write(str(temp_bias)+'))) \n')

                    f.write('(assert (=> (> tmp'+str(j)+str(k)+str(i)+' 0) (= nron'+str(j)+str(k)+str(i)+
                           ' tmp'+str(j)+str(k)+str(i)+'))) \n')
                    f.write('(assert (=> (<= tmp'+str(j)+str(k)+str(i)+' 0) (= nron'+str(j)+str(k)+str(i)+
                           ' 0))) \n')
            
            f.write('\n ;Encoding the output layer neuron \n')           
            for j in range(0, self.dnn.linears[self.no_of_layer-1].out_features):
                
                f.write('(assert (= tmp'+str(self.no_of_layer-1)+str(j)+str(i)+' (+ ')
                for k in range(0, self.dnn.linears[self.no_of_layer-1].in_features):
                    #temp_val = round(float( self.dnn.linears[self.no_of_layer-1].weight[j][k]), 5)
                    temp_val = format(self.dnn.linears[self.no_of_layer - 1].weight[j][k], '.5f')
                    if('e' in str(temp_val)):
                        temp_val = self.remove_exponent(str(temp_val))
                    f.write('(* nron'+str(self.no_of_layer-2)+str(k)+str(i)+' '+str(temp_val)+')')
                #temp_bias = round(float(self.dnn.linears[self.no_of_layer-1].bias[j]), 5)
                temp_bias = format(self.dnn.linears[self.no_of_layer - 1].bias[j], '.5f')
                if('e' in str(temp_bias)):
                    temp_bias = self.remove_exponent(str(temp_bias))
                f.write(' '+str(temp_bias)+'))) \n')
                f.write('(assert (=> (> tmp'+str(self.no_of_layer-1)+str(j)+str(i)+' 0) (= y'+str(j)+str(i)+
                           ' tmp'+str(self.no_of_layer-1)+str(j)+str(i)+'))) \n')
                f.write('(assert (=> (<= tmp'+str(self.no_of_layer-1)+str(j)+str(i)+' 0) (= y'+str(j)+str(i)+
                           ' 0))) \n')
            f.write('\n ;Encoding argmax constraint \n')
            if self.paramDict['regression'] == 'no':
                if self.paramDict['multi_label'] == 'False':
                    for j in range(0, self.no_of_class):
                        for k in range(0, self.no_of_class):
                            if(j == k):
                                f.write('(assert (= d'+str(j)+str(k)+str(i)+' 1)) \n')
                            else:
                                f.write('(assert (=> (>= y'+str(j)+str(i)+' y'+str(k)+str(i)+') (= d'
                                    +str(j)+str(k)+str(i)+' 1))) \n')
                                f.write('(assert (=> (< y'+str(j)+str(i)+' y'+str(k)+str(i)+') (= d'
                                    +str(j)+str(k)+str(i)+' 0))) \n')
                    
                    for j in range(0, self.no_of_class):
                        f.write('(assert (=> (= (+ ')
                        for k in range(0, self.no_of_class):
                            f.write('d'+str(j)+str(k)+str(i)+' ')
                        f.write(') '+str(self.no_of_class)+') (= Class'+str(i)+' '+str(j)+'))) \n')
                else:
                    for j in range(0, self.no_of_class):
                        class_name = self.df.columns.values[self.df.shape[1]-self.no_of_class+j]
                        f.write('(assert (=> (> y'+str(j)+str(i)+' 0.5) (= '+class_name+str(i)+' 1))) \n')
            else:
                f.write('(assert (= Class'+str(i)+' y0'+str(i)+')) \n')

        f.close()


class ConvertDNNSklearn2logic:

    def __init__(self, image_data=False):
        with open('param_dict.csv') as csv_file:
            reader = cv.reader(csv_file)
            self.paramDict = dict(reader)
        if self.paramDict['multi_label'] == 'True':
            self.dnn = load('Model/dnn_model_multi.joblib')
        else:
            self.dnn = load('Model/dnn_model_sklearn')
        self.df = pd.read_csv('OracleData.csv')
        self.no_of_params = int(self.paramDict['no_of_params'])
        self.no_of_hidden_layer = len(self.dnn.coefs_) - 1
        self.num_weight_vector = len(self.dnn.coefs_)
        print(self.num_weight_vector)
        # self.no_of_layer = len(self.dnn.linears)
        self.no_of_class = self.dnn.n_outputs_
        self.bound_cex = literal_eval(self.paramDict['bound_cex'])
        self.bound_all = eval(self.paramDict['bound_all_features'])
        with open('feMinValue.csv') as csv_file:
            reader = cv.reader(csv_file)
            self.feMinVal = dict(reader)
        with open('feMaxValue.csv') as csv_file:
            reader = cv.reader(csv_file)
            self.feMaxVal = dict(reader)
        self.bound_list = eval(self.paramDict['bound_list'])

    def remove_exponent(self, value):
        if 'e-' in value:
            decial = value.split('e')
            ret_val = format(((float(decial[0])) * (10 ** int(decial[1]))), '.5f')
            return ret_val
        else:
            return value

    def funcDNN2logic(self):
        with open('feNameType.csv') as csv_file:
            reader = cv.reader(csv_file)
            feName_type = dict(reader)
        f = open('DNNSmt.smt2', 'w')

        f.write(';Input layer neurons \n')
        for i in range(0, self.no_of_params):
            f.write(';-----------' + str(i) + 'th parameter----------------- \n')
            # Initializing input features
            for j in range(0, self.dnn.n_features_in_):
                tempStr = self.df.columns.values[j]
                fe_type = feName_type[tempStr]
                min_val = self.feMinVal[tempStr]
                max_val = self.feMaxVal[tempStr]
                f.write('(declare-fun ' + self.df.columns.values[j] + str(i) + ' ()')
                if ('int' in fe_type):
                    f.write(' Int) \n')
                    if self.bound_cex and tempStr in self.bound_list:
                        f.write("(assert (and (>= " + tempStr + str(i) + " " + str(
                            int(min_val)) + ")" + " " + "(<= " + tempStr + str(i) + " " + str(int(max_val)) + ")))\n")
                    elif self.bound_cex and self.bound_all:
                        f.write("(assert (and (>= " + tempStr + str(i) + " " + str(
                        int(min_val)) + ")" + " " + "(<= " + tempStr + str(i) + " " + str(int(max_val)) + ")))\n")
                else:
                    f.write(' Real) \n')
                    if self.bound_cex and tempStr in self.bound_list:
                        f.write("(assert (and (>= " + tempStr + str(i) + " " + str(min_val) + ")" + " " + "(<= " + tempStr +
                            str(i) + " " + str(max_val) + ")))\n")
                    elif self.bound_cex and self.bound_all:
                        f.write("(assert (and (>= " + tempStr + str(i) + " " + str(
                        min_val) + ")" + " " + "(<= " + tempStr + str(i) + " " + str(max_val) + ")))\n")
                # f.write('(assert (and (>= '+self.df.columns.values[j]+str(i)+' 0) (<= '+self.df.columns.values[j]+str(i)
                #    +' 1))) \n')

            # Initializing hidden layer neurons
            for j in range(0, self.num_weight_vector - 1):
                for k in range(0, len(self.dnn.coefs_[j][0])):
                    f.write('(declare-fun nron' + str(j) + str(k) + str(i) + ' () Real) \n')
                    f.write('(declare-fun tmp' + str(j) + str(k) + str(i) + ' () Real) \n')
            # Initializing output neurons
            for j in range(0, self.no_of_class):
                f.write('(declare-fun y' + str(j) + str(i) + ' () Real) \n')
                f.write('(declare-fun tmp' + str(self.no_of_hidden_layer) + str(j) + str(i) + ' () Real) \n')
            # Initializing extra variables needed for encoding argmax
            '''
            for j in range(0, self.no_of_class):
                for k in range(0, self.no_of_class):
                    f.write('(declare-fun d'+str(j)+str(k)+str(i)+' () Int) \n')
            '''
            if (self.paramDict['multi_label'] == 'FALSE'):
                if self.paramDict['regression'] == 'no':
                    f.write('(declare-fun Class' + str(i) + ' () Int) \n')
                else:
                    f.write('(declare-fun Class' + str(i) + ' () Real) \n')
                    # f.write('(assert (and (>= Class'+str(i)+' 0) (<= Class'+str(i)+' 1))) \n')

            else:
                for j in range(0, self.no_of_class):
                    class_name = self.df.columns.values[self.df.shape[1] - self.no_of_class + j]
                    f.write('(declare-fun ' + class_name + str(i) + ' () Int) \n')
                    f.write('(assert (and (>= ' + class_name + str(i) + ' 0) (<= ' + class_name + str(i) + ' 1))) \n')

        f.write('(define-fun absoluteInt ((x Int)) Int \n')
        f.write('  (ite (>= x 0) x (- x))) \n')
        f.write('(define-fun absoluteReal ((x Real)) Real \n')
        f.write('  (ite (>= x 0) x (- x))) \n')

        for i in range(0, self.no_of_params):
            f.write(';-----------' + str(i) + 'th parameter----------------- \n')
            f.write('\n ;Encoding the hidden layer neurons \n')
            for j in range(0, self.no_of_hidden_layer):
                for k in range(0, len(self.dnn.coefs_[j][0])):
                    f.write('(assert (= ')
                    f.write('tmp' + str(j) + str(k) + str(i) + ' (+')
                    for l in range(0, len(self.dnn.coefs_[j])):
                        # temp_val = round(float(self.dnn.linears[j].weight[k][l]), 5)
                        temp_val = format(self.dnn.coefs_[j][l][k], '.1f')
                        if ('e' in str(temp_val)):
                            temp_val = self.remove_exponent(str(temp_val))
                        if j == 0:
                            f.write('(* ' + self.df.columns.values[l] + str(i) + ' ' + str(temp_val) + ')')
                        else:
                            f.write('(* nron' + str(j - 1) + str(l) + str(i) + ' ' + str(temp_val) + ') ')

                    # temp_bias = round(float(self.dnn.linears[j].bias[k]), 5)
                    temp_bias = format(self.dnn.intercepts_[j][k], '.1f')
                    if ('e' in str(temp_bias)):
                        temp_bias = self.remove_exponent(str(temp_bias))
                    f.write(str(temp_bias) + '))) \n')

                    f.write('(assert (or ')
                    f.write(' (and (> tmp' + str(j) + str(k) + str(i) + ' 0) (= nron' + str(j) + str(k) + str(i) +
                            ' tmp' + str(j) + str(k) + str(i) + '))')
                    f.write(' (and (<= tmp' + str(j) + str(k) + str(i) + ' 0) (= nron' + str(j) + str(k) + str(i) +
                            ' 0)))) \n')

            f.write('\n ;Encoding the output layer neuron \n')
            for j in range(0, self.dnn.n_outputs_):
                f.write('(assert (= tmp' + str(self.no_of_hidden_layer) + str(j) + str(i) + ' (+ ')
                for k in range(0, len(self.dnn.coefs_[self.no_of_hidden_layer - 1][0])):
                    # temp_val = round(float( self.dnn.linears[self.no_of_layer-1].weight[j][k]), 5)
                    temp_val = format(self.dnn.coefs_[self.no_of_hidden_layer][k][j], '.1f')
                    if ('e' in str(temp_val)):
                        temp_val = self.remove_exponent(str(temp_val))
                    f.write('(* nron' + str(self.no_of_hidden_layer - 1) + str(k) + str(i) + ' ' + str(temp_val) + ')')
                # temp_bias = round(float(self.dnn.linears[self.no_of_layer-1].bias[j]), 5)
                temp_bias = format(self.dnn.intercepts_[self.no_of_hidden_layer][j], '.1f')
                if ('e' in str(temp_bias)):
                    temp_bias = self.remove_exponent(str(temp_bias))
                f.write(' ' + str(temp_bias) + '))) \n')
                # f.write('(assert (or ')
                f.write('(assert (= y' + str(j) + str(i) + ' tmp' + str(self.no_of_hidden_layer) + str(j) + str(
                    i) + '))\n ')
                # f.write(' (and (<= tmp'+str(self.no_of_hidden_layer)+str(j)+str(i)+' 0) (= y'+str(j)+str(i)+
                #           ' 0)))) \n')

            f.write('\n ;Encoding argmax constraint \n')
            if self.paramDict['regression'] == 'no':
                if self.paramDict['multi_label'] == 'FALSE':
                    f.write('(assert (or \n')
                    if self.no_of_class != 1:
                        for j in range(0, self.no_of_class):
                            f.write(' (and (and ')
                            for k in range(0, self.no_of_class):
                                if (j != k):
                                    f.write('(>= y' + str(j) + str(i) + ' y' + str(k) + str(i) + ')')
                            f.write(') (= Class' + str(i) + ' ' + str(j) + '))\n')
                        f.write('))\n')
                    else:
                        f.write(
                            '(and (>= y00 0.5) (= Class' + str(i) + ' 0)) (and (< y00 0.5) (= Class' + str(i) + ' 1))')
                        f.write('))\n')
                else:
                    for j in range(0, self.no_of_class):
                        class_name = self.df.columns.values[self.df.shape[1] - self.no_of_class + j]
                        f.write('(assert (=> (> y' + str(j) + str(i) + ' 0.5) (= ' + class_name + str(i) + ' 1))) \n')
            else:
                f.write('(assert (= Class' + str(i) + ' y0' + str(i) + ')) \n')


        f.close()