#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import os

def main():
  module = AnsibleModule(
      argument_spec = dict(
        state     = dict(default='present', choices=['present']),
        id      = dict(required=False),
        name      = dict(required=False),
        mas_path   = dict(default=None),
        update_cache   = dict(default=False)
        )
      )

  try:
    # Is `mas` installed?
    mas = Mas(module)
    translator = MasProgramTranslator()

    # Are we working with a name or an ID?
    if module.params['id'] and module.params['name']:
        raise Exception("You can't specify both 'id' and 'name' in the same call to mas")

    # Update named cache if required. Do this *before* name conversion.
    # This is a no-op for now until we work out how to distribute a 
    # name to ID lookup list
    if module.params['update_cache']:
      translator.update_cache()

    # Normalise to use an ID everywhere
    if module.params['name']:
        module.params['id'] = translator.convert(module.params['name'])

  except IOError as e:
    module.fail_json(msg=e.message)
  except Exception as e:
    module.fail_json(msg=e.message)

  args = {"changed": False}

  # Installation
  if module.params['state'] == 'present':
    if not mas.is_installed(module.params['id']): 
      err = mas.install(module.params['id'], module.check_mode)
      if err != None:
          module.fail_json(msg=err)
      else:
        args['changed'] = True

  args['id'] = module.params['id']
  if module.params['name']:
    args['name'] = module.params['name']
  module.exit_json(**args)

class Mas(object):

  def __init__(self, module):
    self.module = module
    self.params = module.params
    self.mas_path = None

    # Populate caches
    self.find_mas()
    self._installed = self.cache_installed()

  def cache_installed(self):
    rc, raw_list, err = self.run(["list"])
    rows = raw_list.split("\n")
    installed = {}
    for r in rows:
      r = r.split(" ", 1)
      if len(r) == 2:
        installed[r[1]] = r[0]
    return installed

  def find_mas(self):
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

  def install(self, id, dry_run):
    if not dry_run:
      rc, out, err = self.run(["install", id])
      if rc != 0:
          return "Error installing '{}': {}".format(id, err.rstrip())
    return None

  def is_installed(self, id):
      return id in self._installed.values()

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

  def update_cache(self):
      return True

if __name__ == '__main__':
  main()

