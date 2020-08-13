FROM continuumio/miniconda3

EXPOSE 8080
WORKDIR /app
COPY . .
RUN conda env create -f environment.yml
SHELL ["conda", "run", "-n", "bigfoot-streamlit", "/bin/bash", "-c"]
ENTRYPOINT streamlit run \
    --server.address 0.0.0.0 \
    --server.port 8080 \
    bigfoot_streamlit_app.py
