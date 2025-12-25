from plone.app.testing import PloneWithPackageLayer
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting

import plonetheme.imioapps


PLONETHEME_IMIOAPPS = PloneWithPackageLayer(
    zcml_package=plonetheme.imioapps,
    zcml_filename='testing.zcml',
    gs_profile_id='plonetheme.imioapps:testing',
    name="PLONETHEME_IMIOAPPS")

PLONETHEME_IMIOAPPS_INTEGRATION = IntegrationTesting(
    bases=(PLONETHEME_IMIOAPPS, ),
    name="PLONETHEME_IMIOAPPS_INTEGRATION")

PLONETHEME_IMIOAPPS_FUNCTIONAL = FunctionalTesting(
    bases=(PLONETHEME_IMIOAPPS, ),
    name="PLONETHEME_IMIOAPPS_FUNCTIONAL")
