#include <MicroTFLite.h>
#include "model_data.h"

constexpr size_t kTensorArenaSize = 80 * 1024;
static uint8_t tensor_arena[kTensorArenaSize];

static const tflite::Model*      tfl_model   = nullptr;
static tflite::MicroInterpreter* interpreter = nullptr;
static TfLiteTensor* input  = nullptr;
static TfLiteTensor* output = nullptr;

static tflite::AllOpsResolver resolver;

static const int kImageSize = 784;
static uint8_t   image_buf[kImageSize];
static int       bytes_received = 0;

void setup() {
  Serial.begin(115200);
  delay(2000);

  tfl_model = tflite::GetModel(model_data);
  if (tfl_model->version() != TFLITE_SCHEMA_VERSION) {
    while (true) { ; }
  }

  static tflite::MicroInterpreter static_interpreter(
      tfl_model, resolver, tensor_arena, kTensorArenaSize);
  interpreter = &static_interpreter;

  if (interpreter->AllocateTensors() != kTfLiteOk) {
    while (true) { ; }
  }

  input  = interpreter->input(0);
  output = interpreter->output(0);
  bytes_received = 0;
  Serial.println("READY");
}

void loop() {
  while (Serial.available() > 0 && bytes_received < kImageSize) {
    image_buf[bytes_received++] = (uint8_t)Serial.read();
  }

  if (bytes_received < kImageSize) return;

  bytes_received = 0;

  for (int i = 0; i < kImageSize; i++) {
    input->data.int8[i] = (int8_t)(image_buf[i] - 128);
  }

  if (interpreter->Invoke() != kTfLiteOk) {
    Serial.write((uint8_t)0xFE);
    Serial.write((uint8_t)255);
    return;
  }

  int    predicted = 0;
  int8_t best      = output->data.int8[0];
  for (int i = 1; i < 10; i++) {
    if (output->data.int8[i] > best) {
      best      = output->data.int8[i];
      predicted = i;
    }
  }

  Serial.write((uint8_t)0xFE);
  Serial.write((uint8_t)predicted);
  for (int i = 0; i < 10; i++) {
    Serial.write((uint8_t)output->data.int8[i]);
  }
}