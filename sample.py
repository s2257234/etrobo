import random


class Animal:
    def say(self) -> None:
        raise NotImplementedError()

class Dog(Animal):
    def say(self) -> None:
        print("bark")


class Cat(Animal):
    def say(self) -> None:
        print("meow")

def create_animal() -> Animal:
    if random.random() < 0.5:
        return Dog()
    else:
        return Cat()

animals = []

for _ in range(5):
    animals.append(create_animal())

for animal in animals:
    animal.say()

