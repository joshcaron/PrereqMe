'use strict';

var prereqApp = angular.module('prereqMe', [
	'ngRoute',
	'ngCookies'
]);

prereqApp.config(['$routeProvider', '$locationProvider', function($routeProvider, $locationProvider) {
	$routeProvider
		.when('/', {
			templateUrl: 'views/home.html',
			controller: 'HomeController'
		})
		.when('/schools', {
			templateUrl: 'views/schools.html',
			controller: 'SchoolsController'
		}).when('/schools/:school/departments', {
			templateUrl: 'views/departments.html',
			controller: 'DepartmentsController'
		}).otherwise({
			redirectTo: '/schools'
		});;

	$locationProvider.html5Mode(true);

}]);


prereqApp.run(['$rootScope', function($rootScope) {
	var constants = {
		// API Base URL
		API_BASE_URL: 'http://prereq.local/api',

		// Cookie identifier for getting the saved school id
		SAVED_SCHOOL_COOKIE: 'savedSchoolId'
	};
	$rootScope.constants = constants;
}]);