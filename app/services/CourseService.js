'use strict';

prereqApp.factory('CourseService', ['$http', '$cookies', '$q', '$rootScope', function($http, $cookies, $q, $rootScope) {
	var course = {
		'getAllCourses': function(school, department) {
			var deffered = $q.defer();
			this._getCourseList(school.slug, department.abbreviation)
				.then(function(response) {
					deffered.resolve(response.data);
				}, function(error) {
					deffered.reject('Error getting courses: ' + error.status);
				});

			return deffered.promise;
		},

		'getCourse': function(school, department, number) {
			var deffered = $q.defer();
			this._getCourse(school.slug, department.abbreviation, number)
				.then(function(response) {
					deffered.resolve(response.data);
				}, function(error) {
					deffered.reject('Could not get course: ' + error.status);
				});
			return deffered.promise;
		},

		'_getCourseList': function(slug, abbv) {
			return $http.get($rootScope.constants.API_BASE_URL + '/schools/' + slug + '/departments/' + abbv + '/courses/');
		},

		'_getCourse': function(slug, abbv, number) {
			return $http.get($rootScope.constants.API_BASE_URL + '/schools/' + slug + '/departments/' + abbv + '/courses/' + number);
		}
	};
	return course;
}]);