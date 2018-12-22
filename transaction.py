class Transaction:

  def __init__(self, value, zktoken):
    self.value = value
    self.inputs = {}
    self.outputs = {}
    self.rG = None
    self.s = None
    self.e = None
    self.blidinding_sum = 0
    self.zktoken = zktoken

  def inputs_of(self, wallet):
    if wallet not in self.inputs:
      return []
    return self.inputs[wallet]

  def outputs_of(self, wallet):
    if wallet not in self.outputs:
      return []
    return self.outputs[wallet]

  def add_inputs(self, inputs, wallet):
    if wallet not in self.inputs:
      self.inputs[wallet] = []
    self.inputs[wallet].extend(inputs)

  def add_outputs(self, outputs, wallet):
    # each output should be n sized list
    if wallet not in self.outputs:
      self.outputs[wallet] = []
    self.outputs[wallet].extend(outputs)

  def set_excess(self, rG, s, e):
    self.rG = rG
    self.s = s
    self.e = e

  def to_args(self):
    inputs = [i for _, inputs in self.inputs.items() for i in inputs]
    outputs = [o for _, outputs in self.outputs.items() for o in outputs]
    return (inputs, outputs, self.rG, self.s, self.e)

  def broadcast(self):
    return self.zktoken.ct(*self.to_args())

  def __str__(self):
    s = 'inputs\n'
    for w, inputs in self.inputs.items():
      s = s + w + '\n'
      for i in inputs:
        s += str(i) + '\n'
    s += 'outputs\n'
    for w, outputs in self.outputs.items():
      s = s + w + '\n'
      for o in outputs:
        s += str(o) + '\n'
    s += 'rG: ' + str(self.rG) + '\n'
    s += 's:  ' + str(self.s) + '\n'
    s += 'e:  ' + str(self.e) + '\n'
    s += 'val:' + str(self.value) + '\n'
    return s