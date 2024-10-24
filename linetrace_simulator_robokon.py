import argparse

from etrobo_python import ColorSensor, ETRobo, Hub, Motor, TouchSensor


class LineTracer(object):
    def __init__(self, target: int, power: int) -> None:
        #self.target = target
        #self.power = power
        self.state = 1

    def __call__(
        self,
        right_motor: Motor,
        left_motor: Motor,
        color_sensor: ColorSensor,

    ) -> None:
        #self.run_linetrace_left(right_motor, left_motor, color_sensor)
        #print(color_sensor.get_raw_color())
        print("state",self.state)
        #print(color_sensor.get_brightness())
        motor_count = right_motor.get_count() + left_motor.get_count() // 2
        print(motor_count)
        #print(color_sensor.get_raw_color()[2])

        #S(彩度)を計算する式
        self.S = (max(color_sensor.get_raw_color()) - min(color_sensor.get_raw_color())) / max(color_sensor.get_raw_color())
        #print("S",self.S)

        if self.state == 1: 
            self.run_linetrace_left(right_motor, left_motor, color_sensor)
            if self.S > (0.55):
                self.state = 2
        
        elif self.state == 2:
            if self.S > (0.55):
                #if color_sensor.get_brightness() > 20.0:
                self.run_linetrace_left(right_motor, left_motor, color_sensor) 
            elif self.S < (0.55) and color_sensor.get_brightness() < 15.0:
                self.state = 3

        elif self.state == 3:
            self.run_linetrace_right(right_motor, left_motor, color_sensor)
            if self.S > (0.55) and color_sensor.get_brightness() > 15.0:
                self.state = 4
        
        elif self.state == 4:
            if self.S > (0.55):
                self.run_linetrace_right(right_motor, left_motor, color_sensor)
            elif self.S < (0.55) and color_sensor.get_brightness() < 15.0:
                self.state = 5
        
        elif self.state == 5:
            if self.S < (0.55):
                self.run_linetrace_left(right_motor, left_motor, color_sensor)
            if self.S > (0.55) and color_sensor.get_brightness() > 15.0:
                self.state = 6
        
        elif self.state == 6:
            if self.S > (0.55):
                self.run_linetrace_left(right_motor, left_motor, color_sensor)
            elif self.S < (0.55) and color_sensor.get_brightness() < 15.0:
                self.state = 7
        
        elif self.state == 7:
            self.run_linetrace_right(right_motor, left_motor, color_sensor)
            if self.S > (0.55) and color_sensor.get_brightness() > 15.0:
                self.state = 8
            
    
    def run_linetrace_right(
        self,
        right_motor: Motor,
        left_motor: Motor,
        color_sensor: ColorSensor,
    ) -> None:
        #反射光の測定値を取得
        brightness = color_sensor.get_brightness()

        
        if brightness > 15.0: #反射光の測定値が20以上の場合
            right_motor.set_power(50)
            left_motor.set_power(20)
        else:
            right_motor.set_power(20)
            left_motor.set_power(50)

    def run_linetrace_left(
        self,
        right_motor: Motor,
        left_motor: Motor,
        color_sensor: ColorSensor,
    ) -> None:
        #反射光の測定値を取得
        brightness = color_sensor.get_brightness()

        #print(brightness)
        if brightness > 15.0: #反射光の測定値が20以上の場合
            right_motor.set_power(20)
            left_motor.set_power(50)
        else:
            right_motor.set_power(50)
            left_motor.set_power(20) 



    def run_stop(
        self,
        right_motor: Motor,
        left_motor: Motor,
    ) -> None:
        right_motor.set_power(0)
        left_motor.set_power(0)
        right_motor.set_brake(True)
        left_motor.set_brake(True)

        
        

    

(ETRobo(backend='simulator')
 .add_device('right_motor', device_type='motor', port='B')
 .add_device('left_motor', device_type='motor', port='C')
 .add_device('color_sensor', device_type='color_sensor', port='2')
 .add_handler(LineTracer(target=17, power=30))
 .dispatch(interval=0.01, course='left'))

def run(backend: str, target: int, power: int, pid_p: float, state: int, **kwargs) -> None:
    (ETRobo(backend=backend)
     .add_hub('hub')
     .add_device('right_motor', device_type=Motor, port='B')
     .add_device('left_motor', device_type=Motor, port='C')
     .add_device('touch_sensor', device_type=TouchSensor, port='1')
     .add_device('color_sensor', device_type=ColorSensor, port='2')
     .add_handler(LineTracer(target, power,state))
     .dispatch(**kwargs))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--logfile', type=str, default=None, help='Path to log file')
    args = parser.parse_args()
    run(backend='simulator', target=17, power=30, pid_p=0.2, state = 1, logfile=args.logfile)
