import jinja2
import os
import shutil
import yaml
import sys

def render_block(node_type, template, cloud_def, node_num, node_num_type, aws_yaml, state):
  "Renders a single block in AWS role's main.yml"
  if node_type is not None:
    if state == "present":
      aws_yaml.write("{0}\n\n".format(template.render(exact_count = 1, nodenum = node_num, node_num_type = node_num_type, instance_type = cloud_def[node_type]['instance_type'], aws_region = cloud_def['aws_region'], aws_keypair = cloud_def['aws_keypair'], aws_image = cloud_def['aws_image'])))
    else:
      aws_yaml.write("{0}\n\n".format(template.render(exact_count = 0, nodenum = node_num, node_num_type = node_num_type, instance_type = cloud_def[node_type]['instance_type'], aws_region = cloud_def['aws_region'], aws_keypair = cloud_def['aws_keypair'], aws_image = cloud_def['aws_image'])))
  else:
     aws_yaml.write("{0}\n\n".format(template.render(state = state, aws_region = cloud_def['aws_region'])))
  os.fsync(aws_yaml)


def render_infra(create_or_destroy, cloud_def, aws_yaml, inventory_hosts, machine_hosts, site_def, jenv, template_dir):
  node_num = 0
  if create_or_destroy == "create":
    aws_templates = sorted(os.listdir(template_dir))
    state = "present"
  elif create_or_destroy == "destroy":
    aws_templates_initial = ['00_vpc.j2', '01_sec_group.j2']
    aws_templates = sorted(os.listdir(template_dir), reverse = True)
    state = "present"
    for aws_template in aws_templates_initial:
      current_template = jenv.get_template(aws_template)
      if aws_template == "00_vpc.j2" or aws_template == "01_sec_group.j2":
        node_num_type = 1
        render_block(None, current_template, cloud_def, node_num, node_num_type, aws_yaml, state)
    state = "absent"

  for aws_template in aws_templates:
    current_template = jenv.get_template(aws_template)
    if aws_template == "00_vpc.j2" or aws_template == "01_sec_group.j2":
      node_num_type = 1
      render_block(None, current_template, cloud_def, node_num, node_num_type, aws_yaml, state)
    elif aws_template == "02_node_database.j2":
      node_num_type = 0
      if create_or_destroy == "create":
        site_def.write("  pxc_ips:\n")
      for database_node in range(1, cloud_def['database']['num_databases'] + 1):
        if create_or_destroy == "create":
          machine_hosts.write("{{ ")
          machine_hosts.write("database{0}.results[0].tagged_instances[0].private_ip".format(node_num_type + 1))
          machine_hosts.write(" }} {{")
          machine_hosts.write("database{0}.results[0].item.instance_name".format(node_num_type + 1))
          machine_hosts.write(" }}\n")
          site_def.write("    - {{ ")
          site_def.write("database{0}.results[0].tagged_instances[0].private_ip".format(node_num_type + 1))
          site_def.write(" }}\n")

        node_num += 1
        node_num_type += 1
        render_block("database", current_template, cloud_def, node_num, node_num_type, aws_yaml, state)
        if node_num_type == 1:
          inventory_hosts.write("[pxc_bootstrap]\n")
          inventory_hosts.write("{{ ")
          inventory_hosts.write("database{0}.results[0].tagged_instances[0].public_ip".format(node_num_type))
          inventory_hosts.write(" }} \n\n")
        elif node_num_type == 2:
          inventory_hosts.write("[pxc_node]\n")
          inventory_hosts.write("{{ ")
          inventory_hosts.write("database{0}.results[0].tagged_instances[0].public_ip".format(node_num_type))
          inventory_hosts.write(" }} \n")
        else:
          inventory_hosts.write("{{ ")
          inventory_hosts.write("database{0}.results[0].tagged_instances[0].public_ip".format(node_num_type))
          inventory_hosts.write(" }} \n")
      inventory_hosts.write("\n")
    elif aws_template == "03_node_controller.j2":
      node_num_type = 0
      if create_or_destroy == "create":
        site_def.write("  controller_ips:\n")
      for controller_node in range(1, cloud_def['controller']['num_controllers'] + 1):
        if create_or_destroy == "create":
          machine_hosts.write("{{ ")
          machine_hosts.write("controller{0}.results[0].tagged_instances[0].private_ip".format(node_num_type + 1))
          machine_hosts.write(" }} {{")
          machine_hosts.write("controller{0}.results[0].item.instance_name".format(node_num_type + 1))
          machine_hosts.write(" }}\n")
          site_def.write("    - {{ ")
          site_def.write("controller{0}.results[0].tagged_instances[0].private_ip".format(node_num_type + 1))
          site_def.write(" }}\n")

        node_num += 1
        node_num_type += 1
        render_block("controller", current_template, cloud_def, node_num, node_num_type, aws_yaml, state)
        if node_num_type == 1:
          inventory_hosts.write("[init_controller]\n")
          inventory_hosts.write("{{ ")
          inventory_hosts.write("controller{0}.results[0].tagged_instances[0].public_ip".format(node_num_type))
          inventory_hosts.write(" }} db_init=true \n\n")
          inventory_hosts.write("[controller]\n")
        else:
          inventory_hosts.write("{{ ")
          inventory_hosts.write("controller{0}.results[0].tagged_instances[0].public_ip".format(node_num_type))
          inventory_hosts.write(" }} \n")
      inventory_hosts.write("\n")
    elif aws_template == "04_node_network.j2":
      node_num_type = 0
      for network_node in range(1, cloud_def['network']['num_networks'] + 1):
        node_num += 1
        node_num_type += 1
        render_block("network", current_template, cloud_def, node_num, node_num_type, aws_yaml, state)
        if node_num_type == 1:
          inventory_hosts.write("[network]\n")
          inventory_hosts.write("{{ network.results[0].tagged_instances[0].public_ip }}\n\n")
          if create_or_destroy == "create":
            machine_hosts.write("{{ network.results[0].tagged_instances[0].private_ip }} {{ network.results[0].item.instance_name }}\n")
    elif aws_template =="05_node_compute.j2":
      node_num_type = 0
      for compute_node in range(1, cloud_def['compute']['num_computes'] + 1):
        if create_or_destroy == "create":
          machine_hosts.write("{{ ")
          machine_hosts.write("compute{0}.results[0].tagged_instances[0].private_ip".format(node_num_type + 1))
          machine_hosts.write(" }} {{")
          machine_hosts.write("compute{0}.results[0].item.instance_name".format(node_num_type + 1))
          machine_hosts.write(" }}\n")

        node_num += 1
        node_num_type += 1
        render_block("compute", current_template, cloud_def, node_num, node_num_type, aws_yaml, state)
        if node_num_type == 1:
          inventory_hosts.write("[compute]\n")
        inventory_hosts.write("{{ ")
        inventory_hosts.write("compute{0}.results[0].tagged_instances[0].public_ip".format(node_num_type))
        inventory_hosts.write(" }}\n")
      inventory_hosts.write("\n")
    elif aws_template == "06_benchmark.j2":
      node_num_type = 0
      for benchmark_node in range(1, cloud_def['benchmark']['num_benchmarks'] + 1):
        node_num += 1
        node_num_type += 1
        render_block("benchmark", current_template, cloud_def, node_num, node_num_type, aws_yaml, state)
        if node_num_type == 1:
          inventory_hosts.write("[benchmark]\n")
          inventory_hosts.write("{{ benchmark.results[0].tagged_instances[0].public_ip }}\n")
          if create_or_destroy == "create":
            machine_hosts.write("{{ benchmark.results[0].tagged_instances[0].private_ip }} {{ benchmark.results[0].item.instance_name }}\n")
    elif aws_template == "07_hosts.j2":
      if create_or_destroy == "create":
        node_num_type = 1
        render_block(None, current_template, cloud_def, node_num, node_num_type, aws_yaml, state)
    else:
      sys.exit("Unknown template in templates dir")

cloud_f = open("cloud_def.yml", "r")
aws_yaml_create = open("{0}/roles/aws_create/tasks/main.yml".format(os.getcwd()), "w")
aws_yaml_destroy = open("{0}/roles/aws_destroy/tasks/main.yml".format(os.getcwd()), "w")
inventory_hosts_create = open("{0}/roles/aws_create/templates/inventory_hosts.j2".format(os.getcwd()), "w")
inventory_hosts_destroy = open("{0}/roles/aws_destroy/templates/inventory_hosts.j2".format(os.getcwd()), "w")
machine_hosts = open("{0}/roles/aws_create/templates/machine_hosts.j2".format(os.getcwd()), "w")
machine_hosts.write("127.0.0.1 localhost\n")
shutil.copyfile("{0}/site_def.yml".format(os.getcwd()), "{0}/roles/aws_create/templates/site_def.yml.j2".format(os.getcwd()))
site_def = open("{0}/roles/aws_create/templates/site_def.yml.j2".format(os.getcwd()),"a")

template_dir = "{0}/aws_templates".format(os.getcwd())
cloud_def = yaml.load(cloud_f)

jloader = jinja2.FileSystemLoader(template_dir)
jenv = jinja2.Environment(loader=jloader, trim_blocks=True)

render_infra("create", cloud_def, aws_yaml_create, inventory_hosts_create, machine_hosts, site_def, jenv, template_dir)
render_infra("destroy", cloud_def, aws_yaml_destroy, inventory_hosts_destroy, machine_hosts, site_def, jenv, template_dir)

aws_yaml_create.close()
aws_yaml_destroy.close()
inventory_hosts_create.close()
inventory_hosts_destroy.close()