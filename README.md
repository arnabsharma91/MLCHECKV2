![alt text](https://github.com/arnabsharma91/MLCHECKV2/blob/main/MLCHECK-logo.JPG)

# MLCHECK

This reporsitory contains the code for the tool MLCHECK which has been developed to test machine learning models with respect to specifiedproperties. 

## Usage
To use MLCHECK to test a property you need to first of all upload your model and give the path to the ```model_path``` parameter. MLCHECK needs the input output format of the given model to test, which could be given inside an XML file. There is a sample XML file ```dataInput.xml``` which shows you how to make such an XML file. If you have the training data format available in a dataframe, you could use the following code to generate an XML file in the specific format we require:

```
def funcWriteXml(df):
    f = open('dataInput.xml', 'w')
    f.write('<?xml version="1.0" encoding="UTF-8"?> \n <Inputs> \n')

    for i in range(0, df.shape[1]):
        f.write('<Input> \n <Feature-name>')
        f.write(df.columns.values[i])
        f.write('<\Feature-name> \n <Feature-type>')
        f.write(str(df.dtypes[i]))
        f.write('<\Feature-type> \n <Value> \n <minVal>')
        f.write(str(format(df.iloc[:, i].min(), '.7f')))
        f.write('<\minVal> \n <maxVal>')
        f.write(str(format(df.iloc[:, i].max(), '.7f')))
        f.write('<\maxVal> \n <\Value> \n <\Input>\n')

    f.write('<\Inputs>')
    f.close()
    
```

After you have provided these two, next, we need the list of tha instance variables that you would use to write the property. This will basically help us to connect the property with the specification you have provided. To give you an example, suppose you want to test the fairness property, individual discrimination which requires two input instances to have same values except for the *protected attribute*, and the corresponding outputs remain the same. So, to specify this property, you would need two instance variables. For naming the variables, you could take any permissible variable name in Python. Let us take x and y for this. You need to then specify ```instance_list = ['x', 'y']``` an array of two variable names. You need to specify all these, by calling the function propCheck(). An excerpt of this function and how to load all the other functions can be written as follows:

```
from utils.mlCheck import Assume, Assert, propCheck
propCheck(model_path='Documents/..', instance_list = ['x', 'y'], xml_file='dataInput.xml')
```
Thera are many other parameters which you could set the details of which we describe later.
Once you have specified these three important parameters, you could already start with testing the model. To specify the property you need to use ```Assume``` and ```Assert```. Again let us take the individual discrimination property with x and y as instance variables, and let us assume the instance size is 15 (i.e., the no. of input features are 15) and the protected attribute is gender, then you could specify the property as follows:

```
for i in range(0, 15):
        if feature(i) == 'gender':
            Assume('x[i] != y[i]', i)
        else:
            Assume('x[i] = y[i]', i)
Assert('model.predict(x) == model.predict(y)')
```
So, here we are running the loop to the number of features and if the name of the feature is gender, which could be found by the feature(i) function, then their outputs which is denoted by ```model.predict(..)``` should be same.    

