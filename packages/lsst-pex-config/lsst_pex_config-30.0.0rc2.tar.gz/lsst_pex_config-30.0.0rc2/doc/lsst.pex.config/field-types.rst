.. py:currentmodule:: lsst.pex.config

#############################
Types of configuration fields
#############################

.. TODO: improve this page to summarize the purpose of each field, and then have a dedicated section for each field. https://jira.lsstcorp.org/browse/DM-17196

Attributes of the configuration object must be subclasses of `Field`.
A number of these are predefined: `Field`, `RangeField`, `ChoiceField`, `ListField`, `ConfigField`, `ConfigChoiceField`, `RegistryField`, `ConfigurableField`, `~.configurableActions.ConfigurableActionField`, and `~.configurableActions.ConfigurableActionStructField`.

Example of `RangeField`:

.. code-block:: python

    class BackgroundConfig(pexConfig.Config):
        """Parameters for controlling background estimation.
        """
        binSize = pexConfig.RangeField(
            doc=("Define the region of the sky size "
                 "used for each background point."),
            dtype=int, default=256, min=10
        )

Example of `ListField` and `Config` inheritance:

.. code-block:: python

    class OutlierRejectedCoaddConfig(CoaddTask.ConfigClass):
        """Additional parameters for outlier-rejected coadds.
        """
        subregionSize = pexConfig.ListField(
            dtype=int,
            doc=("Width and height of stack subregion size. Make the values "
                 "small enough that a full stack of images will "
                 "fit into memory at once."),
            length=2,
            default=(200, 200),
            optional=None,
        )

Examples of `ChoiceField` and `ConfigField` and the use of the `Config` object's `Config.setDefaults` and `Config.validate` methods:

.. code-block:: python

    class InitialPsfConfig(pexConfig.Config):
        """A config that describes the initial PSF used
        for detection and measurement (before PSF
        determination is done).
        """

        model = pexConfig.ChoiceField(
            dtype=str,
            doc="PSF model type.",
            default="SingleGaussian",
            allowed={
                "SingleGaussian": "Single Gaussian model",
                "DoubleGaussian": "Double Gaussian model",
            },
        )

    class CalibrateConfig(pexConfig.Config):
        """A config to configure the calibration of an Exposure.
        """
        initialPsf = pexConfig.ConfigField(
            dtype=InitialPsfConfig,
            doc=InitialPsfConfig.__doc__)
        detection = pexConfig.ConfigField(
            dtype=measAlg.SourceDetectionTask.ConfigClass,
            doc="Initial (high-threshold) detection phase for calibration."
        )

        def setDefaults(self):
            self.detection.includeThresholdMultiplier = 10.0

        def validate(self):
            pexConfig.Config.validate(self)
            if self.doComputeApCorr and not self.doPsf:
                raise ValueError("Cannot compute aperture correction "
                                 "without doing PSF determination.")

Examples of `~.configurableActions.ConfigurableActionField` and `~.configurableActions.ConfigurableActionStructField` making use of `~.configurableActions.ConfigurableAction`\ s in a `Config` object.

.. code-block:: python

    class ExampleAction(pexConfig.configurableActions.ConfigurableAction):
        """A ConfigurableAction that performs a simple calculation"""

        numerator = pexConfig.Field[float](doc="Numerator for division operation")
        divisor = pexConfig.Field[float](doc="Divisor for division operation")

        def __call__(self, **kwargs):
            return self.numerator / self.divisor


    class ExampleConfig(pexConfig.Config):
        """An example Config class which contains multiple `ConfigurableAction`\ s."""

        divideAction = pexConfig.configurableActions.ConfigurableActionField(
            doc="A field which points to a single action."
            default=ExampleAction
        )

        multipleDivisionActions = pexConfig.configurableActions.ConfigurableActionStructField(
            doc="A field which acts as a struct, referring to multiple ConfigurableActions."
        )

        def setDefaults(self):
            """Example of setting multiple default configurations with `ConfigurableAction`\ s.
            """
            self.divideAction.numerator = 1
            self.divideAction.divisor = 2

            self.multipleDivisionActions.subDivide1 = ExampleAction()
            self.multipleDivisionActions.subDivide1.numerator = 5
            self.multipleDivisionActions.subDivide1.divisor = 10

            self.multipleDivisionActions.subDivide2 = ExampleAction()
            self.multipleDivisionActions.subDivide2.numerator = 7
            self.multipleDivisionActions.subDivide2.divisor = 8
