import argparse

from etrobo_python import ColorSensor, ETRobo, Hub, Motor, TouchSensor


class State(object):
    def __init__(self)-> None:
        right_instance = Right()
        left_instance = Left()
        self.runners = [
            LineTraceRunner(left_instance.run),
            LineTraceRunner(right_instance.run),
        ]
        self.state = 0
    
    def __call__(
        self,
        hub: Hub,
        arm_motor: Motor,
        right_motor: Motor,
        left_motor: Motor,
        touch_sensor: TouchSensor,
        color_sensor: ColorSensor,

    ) -> None:
        
        if self.state < len(self.runners):
            self.runners[self.state].run(right_motor, left_motor, color_sensor)
        else:
            Brake().run(right_motor, left_motor)
        #self.runners[self.state].run(right_motor, left_motor, color_sensor)

class Linetrace(object):
    def run(
        self,
        right_motor: Motor,
        left_motor: Motor,
        color_sensor: ColorSensor,
    ) -> None:
        raise NotImplementedError()


class LineTraceRunner(Linetrace):
    def __init__(self, run_method) -> None:
        self.run_method = run_method
    
    def run(
        self,
        right_motor: Motor,
        left_motor: Motor,
        color_sensor: ColorSensor,
    ) -> None:
        
        self.run_method(right_motor, left_motor, color_sensor)

    def blue_cheak(
        self,
        color_sensor: ColorSensor,
    ) -> float:
        S = (max(color_sensor.get_raw_color()) - min(color_sensor.get_raw_color())) / max(color_sensor.get_raw_color())
        S = round(self.S, 2)

        return S

class Right(Linetrace):
    def __init__ (self,) -> None:
        pass
    def run(
        self,
        right_motor: Motor,
        left_motor: Motor,
        color_sensor: ColorSensor,
    ) -> None:
        
        #反射光の測定値を取得
        brightness = color_sensor.get_brightness()

        
        if brightness > 15.0: #反射光の測定値が15以上の場合
            right_motor.set_power(50)
            left_motor.set_power(20)
        else:
            right_motor.set_power(20)
            left_motor.set_power(50)

class Left(Linetrace):
    def __init__ (self,) -> None:
        pass
    def run(
        self,
        right_motor: Motor,
        left_motor: Motor,
        color_sensor: ColorSensor,
    ) -> None:
        #反射光の測定値を取得
        brightness = color_sensor.get_brightness()

        
        #print(brightness)
        if brightness > 15.0: #反射光の測定値が15以上の場合
            right_motor.set_power(20)
            left_motor.set_power(50)
            
            
        else:
            right_motor.set_power(50)
            left_motor.set_power(20) 

class Brake(Linetrace):
    def run(
        self,
        right_motor: Motor,
        left_motor: Motor,
    ) -> None:
        right_motor.set_power(0)
        left_motor.set_power(0)
        right_motor.set_brake(True)
        left_motor.set_brake(True)



"""(ETRobo(backend='simulator')
 .add_device('right_motor', device_type='motor', port='B')
 .add_device('left_motor', device_type='motor', port='C')
 .add_device('color_sensor', device_type='color_sensor', port='2')
 .add_handler(State())
 .dispatch(interval=0.01, course='left'))"""

def run(backend: str, target: int, power: int, pid_p: float, state: int, **kwargs) -> None:
    (ETRobo(backend=backend)
     .add_hub('hub')
     .add_device('arm_motor', device_type=Motor, port='A')
     .add_device('right_motor', device_type=Motor, port='B')
     .add_device('left_motor', device_type=Motor, port='C')
     .add_device('touch_sensor', device_type=TouchSensor, port='1')
     .add_device('color_sensor', device_type=ColorSensor, port='2')
     .add_handler(State())
     .dispatch(**kwargs))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--logfile', type=str, default=None, help='Path to log file')
    args = parser.parse_args()
    run(backend='simulator', target=17, power=30, pid_p=0.2, state = 1, logfile=args.logfile)
