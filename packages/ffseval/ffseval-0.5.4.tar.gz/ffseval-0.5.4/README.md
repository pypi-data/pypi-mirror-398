# FFSeval
## Evaluation of fitness for service
#### Shinsuke Sakai   
 Emeritus Professor, The University of Tokyo, Japan   
 Visiting Professor, Yokohama National University, Japan



### Operation check


```python
from FFSeval import FFS as ffs
cls=ffs.Treat()
L=cls.Set('L_2_b')
data={
   'Ri':275e-3,
   't':16e-3,
   'Sy':514,
   'p':8.0,
   'a':11e-3
}
L.SetData(data)
L.Calc()
L.GetRes()
#{'Lr': 0.7709984917738504, 'pc': 10.376155187533834}
```







