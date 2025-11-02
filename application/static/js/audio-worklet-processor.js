// audio-worklet-processor.js
class RecordingProcessor extends AudioWorkletProcessor {
  process(inputs, outputs, parameters) {
    console.log('Worklet process called, inputs length:', inputs.length);
    const input = inputs[0];
    if (input && input.length > 0) {
      const channelData = input[0];
      // Send a copy of the audio data to the main thread
      console.log('Sending audio data, length:', channelData.length);
      this.port.postMessage({
        type: 'audio-data',
        data: channelData.slice()
      });
    }
    return true; // Keep the processor alive
  }
}

registerProcessor('recording-processor', RecordingProcessor);