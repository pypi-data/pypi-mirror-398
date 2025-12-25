from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name = "Apside",
    version= "0.6",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=["numpy", "numba"],
    dependency_links=[],
    author="Venkata Pendyala",
    author_email="venkatasiddharthpendyala@gmail.com",

    entry_points={
        "console_scripts": [
            # Acceleration / forces
            "apside-accel=apside.acceleration:acceleration",

            # Potentials and energy
            "apside-phi-bulge=apside.energy:phiBulge",
            "apside-phi-disk=apside.energy:phiDisk",
            "apside-phi-halo=apside.energy:phiHalo",
            "apside-energy=apside.energy:totalEnergy",

            # Leapfrog integrator
            "apside-half-velocity=apside.leapfrog:halfVelocity",
            "apside-next-pos=apside.leapfrog:nextPos",
            "apside-next-vel=apside.leapfrog:nextVel",
            "apside-leapfrog-step=apside.leapfrog:leapfrogStep",
        ]
}

)