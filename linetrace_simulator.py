import argparse

from etrobo_python import ColorSensor, ETRobo, Hub, Motor, TouchSensor


class LineTracer(object):
    def __init__(self, target: int, power: int, pid_p: float) -> None:
        self.target = target
        self.power = power
        self.pid_p = pid_p
        self.state = 1


    def __call__(
        self,
        right_motor: Motor,
        left_motor: Motor,
        color_sensor: ColorSensor,
        hub: Hub,
        touch_sensor: TouchSensor,

    ) -> None:
        #モーターの回転角度を取得
        right_motor_count = right_motor.get_count()
        left_motor_count = left_motor.get_count()
        print(left_motor_count)

        if self.state == 1:
            self.run_linetrace(right_motor, left_motor, color_sensor)
            if left_motor_count > 3800:
                self.state = 2
        elif self.state == 2:
            #旋回
            right_motor.set_power(-20)
            left_motor.set_power(20) 
            if left_motor_count > 4100:
                self.run_stop(right_motor, left_motor)
                self.state = 3
        elif self.state == 3:
            #ライントレース
            self.run_linetrace(right_motor, left_motor, color_sensor)
            if left_motor_count > 8500:
                self.state = 4
        else:
            #停止
            self.run_stop(right_motor, left_motor)




    def run_linetrace(
        self,
        right_motor: Motor,
        left_motor: Motor,
        color_sensor: ColorSensor,
    ) -> None:
        #反射光の測定値を取得
        brightness = color_sensor.get_brightness()
        self.pd_contorol(right_motor, left_motor, color_sensor)
        if brightness > 20.0: #反射光の測定値が20以上の場合
            right_motor.set_power(50)
            left_motor.set_power(20)
        else:
            right_motor.set_power(20)
            left_motor.set_power(50)
    #逆向きに走る
    def run_back(
        self,
        right_motor: Motor,
        left_motor: Motor,
        color_sensor: ColorSensor,
    ) -> None:
        brightness = color_sensor.get_brightness()
        if brightness > 20.0: #反射光の測定値が20以上の場合
            right_motor.set_power(-50)
            left_motor.set_power(-20)
        else:
            right_motor.set_power(-20)
            left_motor.set_power(-50)
    
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
 .add_handler(LineTracer(target=17, power=30, pid_p=0.2))
 .dispatch(interval=0.01, course='left'))

def run(backend: str, target: int, power: int, pid_p: float, state:int, **kwargs) -> None:
    (ETRobo(backend=backend)
     .add_hub('hub')
     .add_device('right_motor', device_type=Motor, port='B')
     .add_device('left_motor', device_type=Motor, port='C')
     .add_device('touch_sensor', device_type=TouchSensor, port='1')
     .add_device('color_sensor', device_type=ColorSensor, port='2')
     .add_handler(LineTracer(target, power, pid_p, state))
     .dispatch(**kwargs))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--logfile', type=str, default=None, help='Path to log file')
    args = parser.parse_args()
    run(backend='simulator', target=17, power=30, pid_p=0.2, state = 1, logfile=args.logfile)
