# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-09-02 20:29
from __future__ import unicode_literals
import os

from graphviz import Digraph

from django.db import migrations
from django.core.files.base import ContentFile
from django.contrib.contenttypes.management import create_contenttypes

from bayesian_networks.bayespy_constants import (
    DIST_DIRICHLET, DIST_CATEGORICAL, DIST_GAUSSIAN, DIST_WISHART,
    DIST_MIXTURE)
from bayesian_networks.models import BayesianNetwork as BN
from bayesian_networks.models import BayesianNetworkNode as BNN


def generate_bn_image(bn):
    """
    Auxiliary function for generating the image of a BN, as model
    methods are not available in migrations.
    """
    dot = Digraph(comment=bn.name)
    nodes = bn.nodes.all()
    for node in nodes:
        dot.node(name=node.name, label=node.name)
    edges = bn.edges.all()
    for edge in edges:
        dot.edge(str(edge.parent.name),
                 str(edge.child.name))
    dot.format = "png"
    contentfile = ContentFile(dot.pipe())
    image_name = "{0}/{1}".format(
        os.path.join("django_ai", "bayesian_networks"),
        bn.name + ".png")
    bn.image.save(image_name, contentfile)
    bn.save()


def create_clustering_bn_example(apps, schema_editor):
    """
    Create a Bayesian Network from the scratch.
    """
    # Content Types Hackery for ensuring that it exists
    app_config = apps.get_app_config('examples')
    app_config.models_module = app_config.models_module or True
    create_contenttypes(app_config)
    ##

    BayesianNetwork = apps.get_model(
        "bayesian_networks", "BayesianNetwork")
    BayesianNetworkEdge = apps.get_model(
        "bayesian_networks", "BayesianNetworkEdge")
    BayesianNetworkNode = apps.get_model(
        "bayesian_networks", "BayesianNetworkNode")
    BayesianNetworkNodeColumn = apps.get_model(
        "bayesian_networks", "BayesianNetworkNodeColumn")

    ContentType = apps.get_model(
        "contenttypes", "ContentType")

    bn = BayesianNetwork(
        name="Clustering (Example)",
        network_type=BN.TYPE_CLUSTERING,
    )
    bn.save()
    alpha = BayesianNetworkNode(
        network=bn,
        name="alpha",
        node_type=BNN.NODE_TYPE_STOCHASTIC,
        is_observable=False,
        distribution=DIST_DIRICHLET,
        distribution_params="numpy.full(10, 1e-05)",
    )
    Z = BayesianNetworkNode(
        network=bn,
        name="Z",
        node_type=BNN.NODE_TYPE_STOCHASTIC,
        is_observable=False,
        distribution=DIST_CATEGORICAL,
        distribution_params="alpha, plates=(:dl_Y, ), :ifr",
    )
    mu = BayesianNetworkNode(
        network=bn,
        name="mu",
        node_type=BNN.NODE_TYPE_STOCHASTIC,
        is_observable=False,
        distribution=DIST_GAUSSIAN,
        distribution_params=("numpy.zeros(2), [[1e-5,0], [0, 1e-5]], "
                             "plates=(10, )"),
    )
    Lambda = BayesianNetworkNode(
        network=bn,
        name="Lambda",
        node_type=BNN.NODE_TYPE_STOCHASTIC,
        is_observable=False,
        distribution=DIST_WISHART,
        distribution_params="2,  [[1e-5,0], [0, 1e-5]], plates=(10, )",
    )
    Y = BayesianNetworkNode(
        network=bn,
        name="Y",
        node_type=BNN.NODE_TYPE_STOCHASTIC,
        is_observable=True,
        distribution=DIST_MIXTURE,
        distribution_params=("Z, @bayespy.nodes.Gaussian(), "
                             "mu, Lambda, :noplates"),
    )
    alpha.save()
    Z.save()
    mu.save()
    Lambda.save()
    Y.save()
    #
    Y_col_avg_logged = BayesianNetworkNodeColumn(
        node=Y,
        ref_model=ContentType.objects.get(
            model="userinfo", app_label="examples"),
        ref_column="avg_time_logged"
    )
    Y_col_avg_pages_a = BayesianNetworkNodeColumn(
        node=Y,
        ref_model=ContentType.objects.get(
            model="userinfo", app_label="examples"),
        ref_column="avg_time_pages_a"
    )
    Y_col_avg_logged.save()
    Y_col_avg_pages_a.save()
    #
    alpha_to_Z = BayesianNetworkEdge(
        network=bn,
        description="alpha -> Z",
        parent=alpha,
        child=Z
    )
    Z_to_Y = BayesianNetworkEdge(
        network=bn,
        description="Z -> Y",
        parent=Z,
        child=Y
    )
    mu_to_Y = BayesianNetworkEdge(
        network=bn,
        description="mu -> Y",
        parent=mu,
        child=Y
    )
    Lambda_to_Y = BayesianNetworkEdge(
        network=bn,
        description="Lambda -> Y",
        parent=Lambda,
        child=Y
    )
    alpha_to_Z.save()
    Z_to_Y.save()
    mu_to_Y.save()
    Lambda_to_Y.save()
    # Generate the image
    generate_bn_image(bn)


def delete_clustering_bn_example(apps, schema_editor):
    BayesianNetwork = apps.get_model("bayesian_networks",
                                     "BayesianNetwork")

    BayesianNetwork.objects.get(name="Clustering (Example)").delete()


class Migration(migrations.Migration):

    dependencies = [
        ('examples', '0005_add_avg_times_clusters'),
    ]

    operations = [
        migrations.RunPython(create_clustering_bn_example,
                             delete_clustering_bn_example),
    ]
