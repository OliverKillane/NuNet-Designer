# NuNet Designer

![nunetDesigner](https://user-images.githubusercontent.com/44177991/127011353-ea31fa2c-9c8d-4d5f-9526-a09b92a5777a.gif)

A graphical editor to design feedforward neural networks, with a 'no-dependency' library to run them included! Aimed at ML interested students, allowing them to experiment, tinker and learn basic ML concepts without becoming lost in complex maths, or learning little of underlying theory through use of a library.

NuNet Designer:
- Open, create and edit network designs (.nunet files), using a wide range of activation functions, and with named inputs (names used for generated code)
- Uses pygame (using SDL2) for graphics, pickle for design file serialization.
- configuration json allows for very basic theme support, such as background colours, network objects and some text sizes.
- Generates files (optionally adding library file) to run, train and infer from the network designed.

NuNet Library:
- Basic feedforward neural network library (making use of CPU only)
- All functions clearly documented, emphasis on flexibility and readability over speed as the program is intended to be an educational tool for students to tinker and extend as they choose.
- Uses only Random, Math and Collections named tuples (all in standard library), hence generated files can be run anywhere with python 3 (no-dependencies).
