Ansible recipes to setup Openstack benchmarking cluster on AWS. This doesn't actually start vms and the tenant network is not reachable, but all the backend operations will happen. The only purpose of this is to be able to quickly benchmark the openstack's backend.

-----
Tools
-----

To generate all the passwords for Openstack, just do, for the to level directory::

```
./tools/gen_openstack_passwords.sh
```

You need to set up in aws access in .boto.

Set up instance details in roles/aws/vars/main.yml

In order to create instances do:
```
ansible-playbook -i aws_inventory.yml aws.yml
```

This will create the hosts file.

To set up the cluster, run the whole playbook.

```
ansible-playbook -u ubuntu -i hosts site.yml
```

Check hosts file or the AWS console for the machines.
