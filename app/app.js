'use strict';

var prereqApp = angular.module('prereqMe', [
	'ngRoute',
	'ngCookies',
	'ui.bootstrap'
]);

prereqApp.config(['$routeProvider', '$locationProvider', function($routeProvider, $locationProvider) {
	$routeProvider
		.when('/', {
			templateUrl: 'views/home.html',
			controller: 'HomeController'
		})
		.when('/schools/:school', {
			templateUrl: 'views/schoolViewer.html',
			controller: 'SchoolViewerController'
		})
		.when('/schools/:school/departments/:department', {
			templateUrl: 'views/schoolDepartment.html',
			controller: 'SchoolDepartmentController'
		})
		.otherwise({
			redirectTo: '/'
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