<?php

require_once('autoload.php');

// Fired for 404 errors; must be defined before Toro::serve() call
ToroHook::add("404",  function() {
	header('Access-Control-Allow-Origin: *');
	http_response_code(404);
	echo "Sorry :(";
});

Toro::serve(array(
    "/api/" => "Status",

    // Schools Endpoint
    "/api/schools"        => "Schools_All",
    "/api/schools/"       => "Schools_All",
    "/api/schools/:alpha" => "Schools_One",

    // Departments Endpoint
    "/api/schools/:alpha/departments"        => "Schools_Departments_All",
    "/api/schools/:alpha/departments/"       => "Schools_Departments_All",
    "/api/schools/:alpha/departments/:alpha" => "Schools_Departments_One",

    // Courses Endpoint    
    "/api/schools/:alpha/departments/:alpha/courses"         => "Schools_Departments_Courses_All",
    "/api/schools/:alpha/departments/:alpha/courses/"        => "Schools_Departments_Courses_All",
    "/api/schools/:alpha/departments/:alpha/courses/:alpha" => "Schools_Departments_Courses_One"

));
