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
		.when('/schools/:school/departments/:department/courses/:course', {
			templateUrl: 'views/course.html',
			controller: 'CourseController'
		})
		.otherwise({
			redirectTo: '/'
		});;

	$locationProvider.html5Mode(true);

}]);

