
from BaseML import Classification as cls
import joblib
model=cls('MLP',n_hidden=(4,6,4,2))

model.load_dataset('iris_training.csv', type ='csv', x_column = [0,1,2,3],y_column=[4])
model.train(validate=True)
model.save('mymodel.pkl')

y=model.inference([[1,  1,  -1,  0]])
# m=cls('KNN',n_neighbors =3 )
# m.load('mymodel.pkl')
# y=m.inference([[1,  1,  -1,  0]])
print(y)
