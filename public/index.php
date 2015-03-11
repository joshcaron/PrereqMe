<?php

require_once('autoload.php');

// Fired for 404 errors; must be defined before Toro::serve() call
ToroHook::add("404",  function() {
	header('Access-Control-Allow-Origin: *');
	http_response_code(404);
	echo "Sorry :(";
});

Toro::serve(array(
    "/" => "Status",

    // Schools Endpoint
    "/schools"        => "Schools_All",
    "/schools/"       => "Schools_All",
    "/schools/:alpha" => "Schools_One",

    // Departments Endpoint
    "/schools/:alpha/departments"        => "Schools_Departments_All",
    "/schools/:alpha/departments/"       => "Schools_Departments_All",
    "/schools/:alpha/departments/:alpha" => "Schools_Departments_One",

    // Courses Endpoint    
    "/schools/:alpha/departments/:alpha/courses"        => "Schools_Departments_Courses_All",
    "/schools/:alpha/departments/:alpha/courses/"       => "Schools_Departments_Courses_All",
    "/schools/:alpha/departments/:alpha/courses/:alpha" => "Schools_Departments_Courses_One"

));
