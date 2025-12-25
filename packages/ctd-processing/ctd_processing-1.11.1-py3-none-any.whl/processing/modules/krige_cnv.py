import glob
from pathlib import Path

import geopy.distance

# import skgstat as skg
# import utm
import matplotlib.pyplot as plt
import numpy as np
import seabirdfilehandler as sbf
from pykrige.ok import OrdinaryKriging

# TODO add an create list function for seabirdfilehandler
# TODO Lon lat aus zeile lesen, wenn nict vorhanden as header


# Distanz wird aufsummiert


def read_multiple_cnv(input: Path, output: Path = None):
    folder = input

    header_list, data_list, lon_lat_list, max_depth = read_files(folder)

    lon_lat_list = np.array(lon_lat_list)
    distance_list = []

    distance_list.append(0.000)

    for i in range(len(lon_lat_list) - 1):
        distance_list.append(
            round(
                distance_list[i]
                + geopy.distance.geodesic(
                    lon_lat_list[i], lon_lat_list[i + 1]
                ).km,
                3,
            )
        )

    # depth = np.arange(0, len(data_list[0]) / 4, 0.25)

    print(len(distance_list), len(data_list))
    print(distance_list)

    # depth_index = header_list.index("prDM")
    # print(header_list)
    data_column_list = []
    for i in range(len(header_list)):
        data_column = []
        # np.zeros(len(data_list[0]) ,3)
        for j in range(1, len(data_list)):
            one_dataset = np.array(data_list[j][:, i])
            one_dataset = np.c_[
                (
                    np.c_[
                        [
                            distance_list[j]
                            if data_list[j][x][0] is not None
                            else None
                            for x in range(len(one_dataset))
                        ],
                        np.array(data_list[j][:, 0]),
                    ]
                ),
                one_dataset,
            ]
            data_column.append(one_dataset)
        data_column = np.concatenate(data_column)
        data_column_list.append(data_column)

    print(len(data_column_list[8]))

    coulomn = 1
    ok = OrdinaryKriging(
        data_column_list[coulomn][:, 0],
        data_column_list[coulomn][:, 1],
        data_column_list[coulomn][:, 2],
    )

    print(max_depth)
    print(distance_list[-1])

    gridy = np.arange(0, max_depth)
    gridx = np.arange(0, distance_list[-1])

    print(gridy)

    # gridx = distance_list
    # gridy = [x[-1] for x in data_list[8]]

    z, ss = ok.execute("grid", gridx, gridy)
    plt.imshow(z)
    plt.show()

    # [print(x) for x in lon_lat_list]
    # lon_lat_list = np.array(lon_lat_list)
    # x, y = lon_lat_list.T
    # plt.scatter(x, y)
    # plt.show()


def read_files(folder: Path):
    header_list = []
    row_list_list = []
    loc_header_list_list = []
    lon_lat_list = []

    max_nval = 0

    # lon_lat_list.append([data_list[i][:,lon][0], data_list[i][:,lat][0]])
    # x distance, y depth, z value

    for filename in glob.iglob(f"{folder}/*.cnv"):
        local_header_list = []

        nvalues, sbf_names_and_spans, seabirdFile, metadata = setup_sbf(
            filename
        )
        if nvalues > max_nval:
            max_nval = nvalues

        for tuple in sbf_names_and_spans:
            local_header_list.append(tuple[0])
            if tuple[0] not in header_list:
                header_list.append(tuple[0])

        if len(metadata["GPS_Lat"].split(" ")) > 2:
            gps_lat = metadata["GPS_Lat"]
            gps_lon = metadata["GPS_Lon"]

            i = 1
            if gps_lat.split(" ")[1] == "":
                i = 2
            lat = round(
                float(gps_lat.split(" ")[0])
                + (float(gps_lat.split(" ")[i]) / 60),
                3,
            )
            j = 1
            if gps_lon.split(" ")[1] == "":
                j = 2
            lon = round(
                float(gps_lon.split(" ")[0])
                + (float(gps_lon.split(" ")[j]) / 60),
                3,
            )

            lon_lat_list.append([lat, lon])

        else:
            lon_lat_list.append(
                [
                    float(metadata["GPS_Lat"].split(" ")[0]),
                    float(metadata["GPS_Lon"].split(" ")[0]),
                ]
            )

        n = 11
        row_list = []
        i = 0
        for line in seabirdFile.data:
            row_list.append(
                [
                    line[i : i + n].split()[0]
                    for i in range(0, len(line) - n, n)
                ]
            )

        row_list = np.array(row_list, dtype="object")

        row_list_list.append(row_list)
        loc_header_list_list.append(local_header_list)

    np_row_list_list = np.array(row_list_list, dtype="object")

    data_list = []
    for i in range(len(np_row_list_list)):
        # data = np.array([[None for j in range(len(header_list))] for i in range(max_nval)])
        data = np.zeros((len(np_row_list_list[i]), len(header_list)))
        for j in range(len(loc_header_list_list[i])):
            index = header_list.index(loc_header_list_list[i][j])

            data[range(len(np_row_list_list[i][:, j])), index] = (
                np_row_list_list[i][:, j]
            )
        data_list.append(data)

    return header_list, data_list, lon_lat_list, max_nval / 4


def setup_sbf(filename):
    seabirdFile = sbf.SeaBirdFile(filename)
    sbf_names_and_spans = seabirdFile.data_table_names_and_spans
    nvalues = int(seabirdFile.data_table_stats["nvalues"])
    metadata = seabirdFile.metadata

    return nvalues, sbf_names_and_spans, seabirdFile, metadata


if __name__ == "__main__":
    read_multiple_cnv(
        Path(r"C:\Projects\processing\seabird_example_data\cnv\talweg_light")
    )


# if "Pres" in tuple[0] and float(tuple[1].split(',')[1].strip()) > max_depth:
#         max_depth = float(tuple[1].split(',')[1].strip())

# elif "Depth" in tuple[0] and float(tuple[1].split(',')[1].strip()) > max_depth:
#         max_depth = float(tuple[1].split(',')[1].strip())

# print(len(np_row_list_list[i][:,j]))
# print(data[range(len(np_row_list_list[i][:,j])), index])
# print(len(data[range(len(np_row_list_list[i][:,j])), index]))
