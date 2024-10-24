import argparse

from etrobo_python import ColorSensor, ETRobo, Hub, Motor, TouchSensor, GyroSensor, SonarSensor

class Runner:
     def __init__(self, target: int, power: int, pid_p: float) -> None:
        self.line_trace = LineTrace()
        #self.reverse = reverse()
        
     def __call__(
        self,
        right_motor: Motor,
        left_motor: Motor,
        color_sensor: ColorSensor,
        hub: Hub,
        touch_sensor: TouchSensor,
        sonar_sensor: SonarSensor,

    ) -> None:
        self.line_trace.run(right_motor, left_motor, color_sensor, sonar_sensor)

class LineTrace:
    def run(
        self,
        right_motor: Motor,
        left_motor: Motor,
        color_sensor: ColorSensor,
        sonar_sensor: SonarSensor,
        ) -> None:
        if sonar_sensor.listen:
            print(sonar_sensor.get_distance())

        
        brightness = color_sensor.get_brightness()
        if brightness > 20:
            right_motor.set_power(50)
            left_motor.set_power(20)
        else:
            right_motor.set_power(20)
            left_motor.set_power(50)

"""class reverse:
    def run_reverse(
        self,
        right_motor: Motor,
        left_motor: Motor,
        ) -> None:
        if self.left_moter.get_count() > 3800:
            right_motor.set_power(-20)
            left_motor.set_power(20)"""

def run(backend: str, target: int, power: int, pid_p: float, state:int, **kwargs) -> None:
    (ETRobo(backend=backend)
     .add_hub('hub')
     .add_device('right_motor', device_type=Motor, port='B')
     .add_device('left_motor', device_type=Motor, port='C')
     .add_device('touch_sensor', device_type=TouchSensor, port='1')
     .add_device('color_sensor', device_type=ColorSensor, port='2')
     .add_device('sonar_sensor', device_type=SonarSensor, port='6')
     .add_handler(Runner( target, power, pid_p))
     .dispatch(**kwargs))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--logfile', type=str, default=None, help='Path to log file')
    args = parser.parse_args()
    run(backend='simulator', target=17, power=30, pid_p=0.2, state = 1, logfile=args.logfile)
