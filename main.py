#
# Name: Srijita Banerjee
# UIN: 675443340
# CS 341 Program 1 - Spring 2024
# This is a console-based Python program that inputs
# commands from the user and outputs data from the CTA2 L daily ridership database.
# SQL should be used to retrieve and compute most of the information, while Python is
# used to display the results and if the user chooses, to plot as well.
#

import sqlite3
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import math

##################################################################
#
# print_stats
#
# Given a connection to the CTA database, executes various
# SQL queries to retrieve and output basic stats.
#
def print_stats(dbConn):
    dbCursor = dbConn.cursor()
    
    print("General Statistics:")
    
    # Query for # of stations
    dbCursor.execute("Select count(*) From Stations;")
    row = dbCursor.fetchone()
    print("  # of stations:", f"{row[0]:,}")

    # Query for # of stops
    dbCursor.execute("SELECT COUNT(*) FROM Stops;")
    row = dbCursor.fetchone()
    print("  # of stops:", f"{row[0]:,}")

    # Query for total ride entries
    dbCursor.execute("SELECT COUNT(*) FROM Ridership;")
    row = dbCursor.fetchone()
    print("  # of ride entries:", f"{row[0]:,}")

    # Query for date range
    dbCursor.execute("SELECT MIN(SUBSTR(Ride_Date, 1, 10)), MAX(SUBSTR(Ride_Date, 1, 10)) FROM Ridership;")
    row = dbCursor.fetchone()
    print(" date range:", row[0], "-", row[1])

    # Query for total ridership
    dbCursor.execute("SELECT SUM(Num_Riders) FROM Ridership;")
    row = dbCursor.fetchone()
    print(" Total ridership:", f"{row[0]:,}")

##################################################################
#
# command_1
#
# Find all the station names that match the user input.
# The user will be asked to input a partial station name.
# SQL wildcards _ and % are allowed. Output station names in
# ascending order. If no stations are found, print a message
# indicating that no stations were found.
#
def command_1(dbConn):
    dbCursor = dbConn.cursor()

    print("\nEnter partial station name (wildcards _ and %): ", end="")
    partial_station_name = input().strip()

    # Query for matching station names
    dbCursor.execute("SELECT Station_ID, Station_Name FROM Stations WHERE Station_Name LIKE ? ORDER BY Station_Name ASC;",
                     (partial_station_name,))
    rows = dbCursor.fetchall()

    if rows:
        for row in rows:
            print(f"{row[0]} : {row[1]}")
    else:
        print("**No stations found...")

##################################################################
#
# command_2
#
# Given a station name, find the percentage of riders on weekdays, on Saturdays, and on
# Sundays/holidays for that station.
#
def command_2(dbConn):
    dbCursor = dbConn.cursor()

    print("\n\nEnter the name of the station you would like to analyze: ", end="")
    station_name = input().strip()

    # Subquery to retrieve Station_ID based on station_name
    dbCursor.execute("SELECT Station_ID FROM Stations WHERE Station_Name = ?;", (station_name,))
    station_id_result = dbCursor.fetchone()

    if station_id_result:
        station_id = station_id_result[0]

        # Query for ridership data for the specified station
        dbCursor.execute("""
            SELECT 
                SUM(CASE WHEN Type_of_Day = 'W' THEN Num_Riders ELSE 0 END) AS WeekdayRidership,
                SUM(CASE WHEN Type_of_Day = 'A' THEN Num_Riders ELSE 0 END) AS SaturdayRidership,
                SUM(CASE WHEN Type_of_Day = 'U' THEN Num_Riders ELSE 0 END) AS SundayHolidayRidership,
                SUM(Num_Riders) AS TotalRidership
            FROM Ridership
            WHERE Station_ID = ?;
        """, (station_id,))

        row = dbCursor.fetchone()

        if row:
            weekday_ridership = row[0] or 0
            saturday_ridership = row[1] or 0
            sunday_holiday_ridership = row[2] or 0
            total_ridership = row[3] or 0

            # Calculate percentages with a check for zero total_ridership
            weekday_percentage = (weekday_ridership / total_ridership) * 100 if total_ridership != 0 else 0
            saturday_percentage = (saturday_ridership / total_ridership) * 100 if total_ridership != 0 else 0
            sunday_holiday_percentage = (sunday_holiday_ridership / total_ridership) * 100 if total_ridership != 0 else 0

            # Print the results
            print(f"Percentage of ridership for the {station_name} station:")
            print(" Weekday ridership:", f"{weekday_ridership:,}", f"({weekday_percentage:.2f}%)")
            print(" Saturday ridership:", f"{saturday_ridership:,}", f"({saturday_percentage:.2f}%)")
            print(" Sunday/holiday ridership:", f"{sunday_holiday_ridership:,}", f"({sunday_holiday_percentage:.2f}%)")
            print(" Total ridership:", f"{total_ridership:,}")
        else:
            print("**No data found...")
    else:
        print("**No data found...")

##################################################################
#
# command_3
#
# Output the total ridership on weekdays for each station, with station names rather than
# the station IDs. Also show the percentages, taken out of the total ridership on weekdays
# for all the stations. Order the results in descending order by ridership.
#
def command_3(dbConn):
    dbCursor = dbConn.cursor()

    # Query for total weekday ridership for each station
    dbCursor.execute("""
        SELECT 
            s.Station_Name,
            SUM(CASE WHEN r.Type_of_Day = 'W' THEN r.Num_Riders ELSE 0 END) AS WeekdayRidership,
            SUM(r.Num_Riders) AS TotalRidership
        FROM Stations s
        LEFT JOIN Ridership r ON s.Station_ID = r.Station_ID
        GROUP BY s.Station_ID
        ORDER BY WeekdayRidership DESC;
    """)

    rows = dbCursor.fetchall()

    if rows:
        total_weekday_ridership_all_stations = sum(row[1] for row in rows)

        print("Ridership on Weekdays for Each Station")
        for row in rows:
            station_name = row[0]
            weekday_ridership = row[1] or 0
            total_ridership = row[2] or 0

            # Calculate percentage with a check for zero total_weekday_ridership_all_stations
            percentage = (weekday_ridership / total_weekday_ridership_all_stations) * 100 if total_weekday_ridership_all_stations != 0 else 0

            # Print the results
            print(f"{station_name} : {weekday_ridership:,} ({percentage:.2f}%)")
    else:
        print("**No data found...")

##################################################################
#
# command_4
#
# Given a line color and direction, output all the stops for that line color in that direction.
# Order by stop name in ascending order. The line color and direction should be treated
# as case-insensitive.
#
def command_4(dbConn):
    dbCursor = dbConn.cursor()

    print("\n\nEnter a line color (e.g. Red or Yellow):", end=" ")
    line_color = input().strip()

    # Check if the line exists
    dbCursor.execute("SELECT COUNT(*) FROM Lines WHERE Color = ? COLLATE NOCASE;", (line_color,))
    row = dbCursor.fetchone()
    if row[0] == 0:
        print(f"**No such line...")
        return

    print("Enter a direction (N/S/W/E):", end=" ")
    direction = input().strip().upper()  # Convert direction to uppercase



    # Fetch and display stops for the given line color and direction
    query = """
        SELECT Stop_Name, Stops.Direction, CASE WHEN ADA = 1 THEN '(handicap accessible)' ELSE '(not handicap accessible)' END
        FROM Stops
        JOIN StopDetails ON Stops.Stop_ID = StopDetails.Stop_ID
        JOIN Lines ON StopDetails.Line_ID = Lines.Line_ID
        WHERE Lines.Color = ? COLLATE NOCASE
        ORDER BY Stop_Name ASC;
    """
    dbCursor.execute(query, (line_color,))
    stops = dbCursor.fetchall()

    filtered_stops = [(stop[0], stop[1], stop[2]) for stop in stops if stop[1].upper() == direction or stop[1].upper() == 'B']

    if not filtered_stops:
        print(f"**That line does not run in the direction chosen...")
    else:
        for stop in filtered_stops:
            print(f"{stop[0]} : direction = {stop[1]} {stop[2]}")

##################################################################
#
# command_5
#
# Displaying the number of stops for each line color, separated by direction. Showing the results
# in ascending order by color name, and then in ascending order by direction. Also showing
# the percentage for each one, which is taken out of the total number of stops.
#
def command_5(dbConn):
    dbCursor = dbConn.cursor()

    # Fetch and display the number of stops for each line color, separated by direction
    query = """
        SELECT Lines.Color, Stops.Direction, COUNT(*) as Num_Stops
        FROM Stops
        JOIN StopDetails ON Stops.Stop_ID = StopDetails.Stop_ID
        JOIN Lines ON StopDetails.Line_ID = Lines.Line_ID
        GROUP BY Lines.Color, Stops.Direction
        ORDER BY Lines.Color ASC, Stops.Direction ASC;
    """
    dbCursor.execute(query)
    stops_by_color_and_direction = dbCursor.fetchall()

    # Calculate the total number of stops
    total_stops_query = "SELECT COUNT(*) FROM Stops;"
    dbCursor.execute(total_stops_query)
    total_stops = dbCursor.fetchone()[0]

    # Display the results with percentages
    print("Number of Stops For Each Color By Direction")
    for stop in stops_by_color_and_direction:
        color, direction, num_stops = stop
        percentage = (num_stops / total_stops) * 100
        print(f"{color} going {direction} : {num_stops} ({percentage:.2f}%)")
##################################################################
#
# command_6
#
# Given a station name, displays the total ridership for each year for that station, in
# ascending order by year. Allows the user to use wildcards _ and % for partial names.
# Shows an error message if the station name does not exist or if multiple station names
#match.
# After the output, the user is given the option to plot the data. The axis labels
# and title of the figure are set appropriately. If the user responds with any input other than
# “y”, graph is not plotted.
#
def command_6(dbConn):
    dbCursor = dbConn.cursor()

    print("\nEnter a station name (wildcards _ and %):", end=" ")
    station_name_input = input().strip()

    # Check if the station exists and retrieve details
    query_station = """
        SELECT Station_ID, Station_Name
        FROM Stations
        WHERE Station_Name LIKE ?;
    """
    dbCursor.execute(query_station, (station_name_input,))
    stations = dbCursor.fetchall()

    if len(stations) == 0:
        print("**No station found...")
        return
    elif len(stations) > 1:
        print("**Multiple stations found...")
        return

    station_id, station_name = stations[0]

    # Retrieve and display yearly ridership for the specified station
    query_ridership = """
        SELECT strftime('%Y', Ride_Date) as Year, SUM(Num_Riders) as Total_Riders
        FROM Ridership
        WHERE Station_ID = ?
        GROUP BY Year
        ORDER BY Year ASC;
    """
    dbCursor.execute(query_ridership, (station_id,))
    ridership_data = dbCursor.fetchall()

    print(f"Yearly Ridership at {station_name}")
    for year, total_riders in ridership_data:
        print(f"{year} : {total_riders:,}")

    # Plot the data if the user chooses to do so
    plot_choice = input("\nPlot? (y/n) ").strip().lower()
    if plot_choice == 'y':
        plot_station_ridership(station_name, ridership_data)

def plot_station_ridership(station_name, ridership_data):
    years = [int(year) for year, _ in ridership_data]
    total_riders = [total_riders for _, total_riders in ridership_data]

    plt.plot(years, total_riders, marker='o')
    plt.title(f"Yearly Ridership at {station_name} Station")
    plt.xlabel("Year")
    plt.ylabel("Number of Riders")
    #plt.yticks([i * 200000 for i in range(10)], [f"{i * 0.2:.1f}" for i in range(10)])
    plt.grid(True)
    plt.show()
##################################################################
#
# command_7
#
# Given a station name and year, this command displays the total ridership for each month in that year.
# The user should be able to enter SQL wildcards (_ and %) for the station name.
# Once the station name and year have been entered, the monthly totals are displayed. Then,
# the user is given the option to see a plot of the results. If the user responds with “y” the
# program plots the appropriate graph. If
# the user responds with any other input, nothing is plotted.
# If no matching station names are found, or if multiple matching station names are found,
# the corresponding error messages are displayed. If the user enters a year for which
# there is no data, no error message is necessary. The output and plot will be empty,
# which is sufficient.
#
def command_7(dbConn):
    dbCursor = dbConn.cursor()

    print("\nEnter a station name (wildcards _ and %):", end=" ")
    station_name_input = input().strip()

    # Check if the station exists and retrieve details
    query_station = """
        SELECT Station_ID, Station_Name
        FROM Stations
        WHERE Station_Name LIKE ?;
    """
    dbCursor.execute(query_station, (station_name_input,))
    stations = dbCursor.fetchall()

    if len(stations) == 0:
        print("**No station found...")
        return
    elif len(stations) > 1:
        print("**Multiple stations found...")
        return

    station_id, station_name = stations[0]

    print("Enter a year:", end=" ")
    year_input = input().strip()

    # Retrieve and display monthly ridership for the specified station and year
    query_ridership = """
        SELECT strftime('%m/%Y', Ride_Date) as Month_Year, SUM(Num_Riders) as Total_Riders
        FROM Ridership
        WHERE Station_ID = ? AND strftime('%Y', Ride_Date) = ?
        GROUP BY Month_Year
        ORDER BY Month_Year ASC;
    """
    dbCursor.execute(query_ridership, (station_id, year_input))
    monthly_ridership_data = dbCursor.fetchall()

    #if not monthly_ridership_data:
        #print("Monthly Ridership at {station_name} for {year_input}")
        #return

    print(f"Monthly Ridership at {station_name} for {year_input}")
    for month_year, total_riders in monthly_ridership_data:
        print(f"{month_year} : {total_riders:,}")

    # Plot the data if the user chooses to do so
    plot_choice = input("\nPlot? (y/n) ").strip().lower()
    if plot_choice == 'y':
        plot_monthly_ridership(station_name, year_input, monthly_ridership_data)

def plot_monthly_ridership(station_name, year, monthly_ridership_data):
    months = [month for month, _ in monthly_ridership_data]
    total_riders = [total_riders / 1000 for _, total_riders in monthly_ridership_data]  # Convert to thousands

    plt.plot(months, total_riders, marker='o', label=f"{station_name} ({year})")
    plt.title(f"Monthly Ridership at {station_name} Station ({year})")
    plt.xlabel("Month")
    plt.ylabel("Number of Riders")
    plt.legend()
    plt.grid(True)
    plt.show()

##################################################################
#
# command_8
#
# Given two station names and year, output the total ridership for each day in that year.
# The user should be able to enter SQL wildcards (_ and %) for each station name. Since
# the full output would be quite long, you should only output the first 5 days and last 5
# days of data for each station. Also give the user the option to see a plot of the results. If
# the user responds with “y” your program should plot as shown below (with appropriate
# title, legend, and axis labels). If the user responds with any other input, do not plot.
# If no matching station names are found, or if multiple matching station names are found,
# display the corresponding error message. Note that if the user enters a year for which
# there is no data, no error message is necessary. The output and plot will be empty,
# which is sufficient.
#

def execute_query(dbCursor, query, params=None):
    if params:
        dbCursor.execute(query, params)
    else:
        dbCursor.execute(query)
    return dbCursor.fetchall()

def get_ridership_data(dbCursor, station_id, year):
    query = """
    SELECT strftime('%Y-%m-%d', Ride_Date) AS Ride_Date, Num_Riders
    FROM Ridership
    WHERE Station_ID = ? AND Ride_Date LIKE ?;
    """
    params = (station_id, f"{year}-%")
    return execute_query(dbCursor, query, params)

def plot_daily_ridership(station_names, years, ridership_data):
    plt.figure(figsize=(10, 6))

    for i, (station_name, year) in enumerate(zip(station_names, years)):
        dates, num_riders = zip(*ridership_data[i])
        plt.plot(dates, num_riders, marker='o', label=f"{station_name} ({year})")

    plt.title(f"Ridership of each day of {year}")
    plt.xlabel("Day")
    plt.ylabel("Number of riders")
    plt.legend()
    plt.xticks(range(0, 366, 50), range(0, 366, 50))
    plt.yticks([i * 2000 for i in range(7)], [f"{i * 2000}" for i in range(7)])
    plt.grid(True)
    plt.show()

def command_8(dbConn):
    dbCursor = dbConn.cursor()

    year_to_compare = input("\nYear to compare against? ")
    station_name_1 = input("\nEnter station 1 (wildcards _ and %): ")
    
    # Get station IDs for the given station names
    station_id_1_query = "SELECT Station_ID, Station_Name FROM Stations WHERE Station_Name LIKE ?;"
    station_ids_1 = execute_query(dbCursor, station_id_1_query, (station_name_1,))

    if len(station_ids_1) > 1:
        print("**Multiple stations found...")
        return
    if len(station_ids_1) == 0:
        print("**No station found...")
        return

    station_id_1, station_name_1 = station_ids_1[0]
    

    station_name_2 = input("\nEnter station 2 (wildcards _ and %): ")
    
    # Get station IDs for the second station name
    station_id_2_query = "SELECT Station_ID, Station_Name FROM Stations WHERE Station_Name LIKE ?;"
    station_ids_2 = execute_query(dbCursor, station_id_2_query, (station_name_2,))

    if len(station_ids_2) > 1:
        print("**Multiple stations found...")
        return
    if len(station_ids_2) == 0:
        print("**No station found...")
        return
    station_id_2, station_name_2 = station_ids_2[0]
    

    ridership_data_1 = get_ridership_data(dbCursor, station_id_1, year_to_compare)
    ridership_data_2 = get_ridership_data(dbCursor, station_id_2, year_to_compare)

    print(f"Station 1: {station_id_1} {station_name_1}")
    for date, num_riders in ridership_data_1[:5] + ridership_data_1[-5:]:
        print(f"{date} {num_riders}")
    
    print(f"Station 2: {station_id_2} {station_name_2}")
    for date, num_riders in ridership_data_2[:5] + ridership_data_2[-5:]:
        print(f"{date} {num_riders}")

    plot_choice = input("\nPlot? (y/n) ").lower()
    if plot_choice == 'y':
        plot_daily_ridership([station_name_1, station_name_2], [year_to_compare, year_to_compare],
                             [ridership_data_1, ridership_data_2])

##################################################################
#
# command_9
#
# Given a set of latitude and longitude from the user, find all stations within a mile square
# radius. Give the user the option to plot these stations on a map as shown below.
# heck that the latitude and longitude are within the bounds of Chicago. The latitude
# should be between 40 and 43 degrees, and the longitude should be between -87 and -
# 88 degrees (yes, these are quite generous boundaries). If either of these is not the
# case, display the appropriate message.
#
# To find stations within a mile radius, the following information will be helpful:
# • Each degree of latitude is approximately 69 miles (111 kilometers) apart
# (https://oceanservice.noaa.gov/facts/latitude.html).
# • Using the formula: miles = cosine(degrees of latitude) · 69.17
# we find that each degree of longitude in Chicago is approximately 51 miles apart
# (https://www.redrockcanyonlv.org/wp-content/uploads/topographic-map-activity-6-miles-for-a-degree-of-longitude-072820.pdf).
#
# This information should help you determine the boundaries of a square mile radius
# around the latitude and longitude entered. Round the numbers so that they have 3 digits
# after the decimal (this improves the results). You can now find all stations located within
# those bounds using SQL.
# If the user chooses to view the plot, the locations of the stations are seen overlaying a
# map of Chicagoland. 
#
def execute_query(dbCursor, query, params=None):
    if params:
        dbCursor.execute(query, params)
    else:
        dbCursor.execute(query)
    return dbCursor.fetchall()

def get_stations_within_mile(dbCursor, latitude, longitude):
    # Check if latitude and longitude are within bounds
    if not (40 <= latitude <= 43) or not (-88 <= longitude <= -87):
        print("**Latitude or longitude entered is out of bounds...")
        return []

    # Calculate boundaries for a square mile radius
    lat_mile = 1 / 69.17
    lon_mile = 1 / (51.0 * math.cos(math.radians(latitude)))

    lat_boundaries = [round(latitude - lat_mile, 3), round(latitude + lat_mile, 3)]
    lon_boundaries = [round(longitude - lon_mile, 3), round(longitude + lon_mile, 3)]

    # Get stations within the boundaries, ordered alphabetically by station names
    query = """
    SELECT DISTINCT Stations.Station_Name, Stops.Latitude, Stops.Longitude
    FROM Stops
    JOIN Stations ON Stops.Station_ID = Stations.Station_ID
    WHERE Stops.Latitude BETWEEN ? AND ?
    AND Stops.Longitude BETWEEN ? AND ?
    ORDER BY Stations.Station_Name;
    """
    params = (lat_boundaries[0], lat_boundaries[1], lon_boundaries[0], lon_boundaries[1])
    return execute_query(dbCursor, query, params)



def plot_stations_on_map(stations):
    x = [station[2] for station in stations]  # longitude
    y = [station[1] for station in stations]  # latitude

    image = plt.imread("chicago.png")
    xydims = [-87.9277, -87.5569, 41.7012, 42.0868]  # area covered by the map

    plt.imshow(image, extent=xydims)
    plt.title("Stations near you")
    plt.scatter(x, y, marker='o', color='red')  # Scatter plot of stations
    for station in stations:
        plt.annotate(station[0], (station[2], station[1]), textcoords="offset points", xytext=(0, 5), ha='center')

    plt.xlim([-87.9277, -87.5569])
    plt.ylim([41.7012, 42.0868])
    plt.show()

def command_9(dbConn):
    dbCursor = dbConn.cursor()

    latitude_str = input("Enter a latitude: ")
    longitude_str = input("Enter a longitude: ")

    try:
        latitude = float(latitude_str)
        longitude = float(longitude_str)
    except ValueError:
        print("**Invalid input for latitude or longitude...")
        return

    stations_within_mile = get_stations_within_mile(dbCursor, latitude, longitude)

    if stations_within_mile:
        print("List of Stations Within a Mile")
        for station in stations_within_mile:
            print(f"{station[0]} : ({station[1]}, {station[2]})")

        plot_choice = input("Plot? (y/n) ").lower()
        if plot_choice == 'y':
            plot_stations_on_map(stations_within_mile)

##################################################################
#
# main
#
print('** Welcome to CTA L analysis app **')
print()

dbConn = sqlite3.connect('CTA2_L_daily_ridership.db')

print_stats(dbConn)

# Command Loop
while True:
    print("\nPlease enter a command (1-9, x to exit): ", end="")
    command = input().strip().lower()

    if command == 'x':
        break
    elif command == '1':
        command_1(dbConn)
    elif command == '2':
        command_2(dbConn)
    elif command == '3':
        command_3(dbConn)
    elif command == '4':
        command_4(dbConn)
    elif command == '5':
        command_5(dbConn)
    elif command == '6':
        command_6(dbConn)
    elif command == '7':
        command_7(dbConn)
    elif command == '8':
        command_8(dbConn)
    elif command == '9':
        command_9(dbConn)
    else:
        print("**Error, unknown command, try again...")

# Close the database connection
dbConn.close()