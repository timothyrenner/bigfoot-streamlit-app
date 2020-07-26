FROM continuumio/miniconda3

EXPOSE 8501
WORKDIR /app
COPY . .
RUN wget "https://raw.githubusercontent.com/timothyrenner/bigfoot-dash-app/master/data/bfro_report_locations.csv"
RUN conda env create -f environment.yml
SHELL ["conda", "run", "-n", "bigfoot-streamlit", "/bin/bash", "-c"]
ENTRYPOINT streamlit run bigfoot_streamlit_app.py
