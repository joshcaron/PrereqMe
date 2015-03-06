'use strict';

prereqApp.factory('DepartmentService', ['$http', '$cookies', '$q', '$rootScope', function($http, $cookies, $q, $rootScope) {
	var department = {
		// Stored departments by school
		stored: {},

		'getDepartmentsForSchool': function(school) {
			var deffered = $q.defer();
			var DepartmentService = this;
			if (this.stored[school.slug] !== undefined) {
				console.log("Loaded departments from cache");
				deffered.resolve(this.stored[school.slug]);
			} else {
				this._getDepartmentList(school.slug)
					.then(function(response) {
						console.log("Got departments from API");
						DepartmentService.stored[school.slug] = response.data;
						deffered.resolve(response.data);
					}, function(error, status) {
						deffered.reject('Failed to get departments:' + status);
					});
			}
			return deffered.promise;
		},

		'_getDepartmentList': function(slug) {
			console.log("Getting departments");
			return $http.get($rootScope.constants.API_BASE_URL + '/schools/' + slug + '/departments');
		},

		'_getDepartmentByAbbv': function(slug, abbv) {
			return $http.get($rootScope.constants.API_BASE_URL + '/schools/' + slug + '/departments/' + abbv);
		}

	};
	return department;
}]);