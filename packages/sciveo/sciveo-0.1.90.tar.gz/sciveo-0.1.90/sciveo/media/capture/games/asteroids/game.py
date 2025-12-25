from space_asteroids import SpaceAsteroids


def main():

  space = SpaceAsteroids(1200, 800, rocket_lives=20)
  space.run()


if __name__=='__main__':
  main()