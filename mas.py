#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import os

def main():
  module = AnsibleModule(
      argument_spec = dict(
        state     = dict(default='present', choices=['present', 'absent']),
        name      = dict(required=True),
        mas_path   = dict(default=None)
        )
      )

  mas = Mas(module)

  # Is `mas` installed?
  try:
    mas.check_installed()
  except IOError as e:
    module.fail_json(msg=e.message)
  except Exception as e:
    module.fail_json(msg=e.message)

  # At this point we can run commands
  list = MasCommandList(module)

  if module.params['state'] == 'present':
    if list.is_installed(module.params['name']): 
      module.exit_json(changed=False, name=module.params['name'])
    else:
      translator = MasProgramTranslator()
      MasCommandInstall(module, translator, module.params['name'])

  #if module.check_mode:
  #    module.exit_json(changed=True, check_mode=True)

  module.exit_json(changed=True, something_else=12345)

class Mas(object):

  def __init__(self, module):
    self.module = module
    self.params = module.params
    self.mas_path = None

  def check_installed(self):
    path = self.params['mas_path']
    if path is None:
      path = 'mas'

    # They may have given us a direct path
    if path[0] == '/':
      possible_paths = [path]
    else:
      possible_paths = [(pre + "/" + path) for pre in os.environ['PATH'].split(":")]

    found_mas = False
    for p in possible_paths:
      if os.access(p, os.X_OK):
        self.mas_path = p
        break

    if self.mas_path == None:
      raise IOError("Could not find the MAS binary")

    rc, out, err = self.run(["account"])
    if out.rstrip() == 'Not signed in':
      raise Exception("You must sign in to the Mac App Store")

    return True

  def run(self, cmd):
    cmd.insert(0, self.mas_path)
    return self.module.run_command(cmd, False)

class MasCommandList(Mas):
  def __init__(self, module):
    super(MasCommandList, self).__init__(module)
    self.check_installed()
    rc, out, err = self.run(["list"])
    self.raw_list = out
    self._installed = None

  def process(self):
    if self._installed is None:
      rows = self.raw_list.split("\n")
      self._installed = {}
      for r in rows:
        r = r.split(" ", 1)
        if len(r) == 2:
          self._installed[r[1]] = r[0]

    return self._installed

  def raw(self):
    return self.process()

  def is_installed(self, name):
      return name in self.process()

class MasCommandInstall(Mas):
  def __init__(self, module, translator, name):
    super(MasCommandInstall, self).__init__(module)
    self.translator = translator
    self.check_installed()
    self.install(name)

  def install(self, name):
    rc, out, err = self.run(["install", self.translator.convert(name)])
    #print out
    # 411246225 Caffeine

class MasProgramTranslator(object):
  def __init__(self):
    self.list ={
      "iA Writer Classic":       439623248,
      "Xcode":                   497799835,
      "ReadKit":                 588726889,
      "Todoist":                 585829637,
      "Caffeine":                411246225,
    }

  def convert(self, name):
    if name in self.list:
      return str(self.list[name])
    raise Exception("Unable to find the application '{}'".format(name))


if __name__ == '__main__':
  main()

