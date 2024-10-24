import argparse

from etrobo_python import ColorSensor, ETRobo, Hub, Motor, TouchSensor


class Runner(object):
    def run(
        self,         
        right_motor: Motor,
        left_motor: Motor,
        color_sensor: ColorSensor,
    ) -> None:
        raise NotImplementedError()

    def check(
        self,         
        right_motor: Motor,
        left_motor: Motor,
        color_sensor: ColorSensor,
    ) -> bool:
        raise NotImplementedError()


class LineTraceRunner(Runner):
    def __init__(self, power: int, count: int) -> None:
        self.power = power
        self.count = count
        self.prev = 0
    
    def run(
        self,         
        right_motor: Motor,
        left_motor: Motor,
        color_sensor: ColorSensor,
    ) -> None:
        red, _, _ = color_sensor.get_raw_color()
        curr = red - 50

        direction = curr * 0.2 + (curr - self.prev) * 2.0
        self.prev = curr

        if direction > 0:
            left_motor.set_power(self.power)
            right_motor.set_power(int(self.power // (1 + abs(direction))))
        else:
            left_motor.set_power(int(self.power // (1 + abs(direction))))
            right_motor.set_power(self.power)

    def check(
        self,         
        right_motor: Motor,
        left_motor: Motor,
        color_sensor: ColorSensor,
    ) -> bool:
        count = (right_motor.get_count() + left_motor.get_count()) // 2
        return count >= self.count


class LineTracer(object):
    def __init__(self) -> None:
        self.runnsers = [
            LineTraceRunner(100, 3000),
            LineTraceRunner(70, 4500),
        ]
        self.state = 0

    def __call__(
        self,
        hub: Hub,
        right_motor: Motor,
        left_motor: Motor,
        touch_sensor: TouchSensor,
        color_sensor: ColorSensor,
    ) -> None:
        if self.state < len(self.runnsers):
            if self.runnsers[self.state].check(
                    right_motor, left_motor, color_sensor):
                self.state += 1

        if self.state < len(self.runnsers):
            self.runnsers[self.state].run(
                right_motor, left_motor, color_sensor)
        else:
            left_motor.set_power(0)
            left_motor.set_brake(True)
            right_motor.set_power(0)
            right_motor.set_brake(True)


def run(backend: str, **kwargs) -> None:
    (ETRobo(backend=backend)
     .add_hub('hub')
     .add_device('right_motor', device_type=Motor, port='B')
     .add_device('left_motor', device_type=Motor, port='C')
     .add_device('touch_sensor', device_type=TouchSensor, port='1')
     .add_device('color_sensor', device_type=ColorSensor, port='2')
     .add_handler(LineTracer())
     .dispatch(**kwargs))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--logfile', type=str, default=None, help='Path to log file')
    args = parser.parse_args()
    run(backend='simulator', logfile=args.logfile)