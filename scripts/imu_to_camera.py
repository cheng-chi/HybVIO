import numpy as np

data = [-0.999997, 0.00187569, 0.00184115,  -0.000269638, 
           -0.00184106, 4.99428e-05, -0.999998, -0.00853536,
          -0.00187578, -0.999998, -4.64894e-05, -0.00305681,
          0.0, 0.0, 0.0, 1.0]
t_imu_camera = np.array(data).reshape(4,4)
t_camera_imu = np.linalg.inv(t_imu_camera)

# column-major
out_data = t_camera_imu.T.flatten().tolist()

txt = ','.join([str(x) for x in out_data])
print(txt)
