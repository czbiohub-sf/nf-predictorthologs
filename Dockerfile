FROM nfcore/base:1.9
LABEL authors="Olga Botvinnik" \
      description="Docker image containing all software requirements for the nf-core/predictorthologs pipeline"

# Install the conda environment
COPY environment.yml /
RUN conda env create -f /environment.yml && conda clean -a

# Dump the details of the installed packages to a file for posterity
RUN conda env export --name nf-core-predictorthologs-1.0dev > nf-core-predictorthologs-1.0dev.yml

# Avoid this error:
# WARNING: Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.
# https://stackoverflow.com/a/48690137/1628971
COPY docker/sysctl.conf /etc/sysctl.conf

# Add conda installation dir to PATH (instead of doing 'conda activate')
ENV PATH /opt/conda/envs/nf-core-predictorthologs-1.0dev/bin:$PATH

RUN echo 'export "PATH=/opt/conda/envs/nf-core-predictorthologs-1.0dev/bin:$PATH"' >> ~/.bashrc

RUN mkdir $HOME/tmp/numba_cache & chmod 777 $HOME/tmp/numba_cache & export NUMBA_CACHE_DIR=/tmp/numba_cache
RUN echo 'export "NUMBA_CACHE_DIR=/tmp/numba_cache"' >> ~/.bashrc
