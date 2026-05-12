# Running-Dense-Neural-Network-in-ESP-32-for-MNIST-digit-recognition

**Hi, my name is Chinmoy Majumder. And I'm a 11th grade student from India. Thanks for using my repository, feel free to experiment, implement and make suggestions for further improvement.**

Here, I will show you step by step how we can run inference of a deep learning model for digit recognition in the stadard ESP-32 microcontroller. 

**Note:- This is soley based on learning and experimentation, we may not expect high quality resulsts**

To make the approach cleaner, we will use the Arduino IDE to make it simple. 
- Search MicroTFLite in the library manager and install it.
- Then, download the given esp32_dnn folder and open the .ino file using the IDE (model_data.h must be in the same folder).
- Compile it, flash it to the ESP-32 and open another IDE for running python like VS Code or PyCharm.
- Run this command in your terminal -> pip install pyserial numpy Pillow
- Now run the given python file "digit input.py"
- Voila! now you can test the model by drawing digits yoursel...

Thank you.
