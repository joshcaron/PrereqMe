'use strict';

prereqApp.factory('SchoolService', ['$http', '$q', '$routeParams', 'config', function($http, $q, $routeParams, config) {
	var school = {
		// Cache of school objects
		schools: [],
		// Cached school object
		savedSchool: null,

		'getSchoolList': function() {
			var deffered = $q.defer();
			var SchoolService = this;
			if (this.schools.length > 0) {
				console.log('Loaded school list from cache.');
				deffered.resolve(this.schools);
			} else {
				this._getSchoolList().then(function(response) {
					console.log('Got school list from API.');
					SchoolService._setSchoolList(response.data);
					deffered.resolve(response.data);
				}, function(response) {
					deffered.reject('Failed to get school list.');
				});
			}

			return deffered.promise;
		},

		'getSchoolBySlug': function(slug) {
			var deffered = $q.defer();

			if (this.savedSchool !== null && this.savedSchool.slug == slug) {
				deffered.resolve(this.savedSchool);
			} else if (this.schools.length != 0) {
				var found = _.find(this.schools, function(school) {
					return school.slug == slug;
				});
				if (found) {
					deffered.resolve(found);
				} else {
					deffered.reject('School not found in cache.');
				}
			} else {
				var SchoolService = this;
				this._getSchoolBySlug(slug).then(function(response) {
					deffered.resolve(response.data);
				}, function (error, status) {
					deffered.reject('Could not get school - ' + status);
				});
			}

			return deffered.promise;
		},

		'getSavedSchool': function() {
			// Order
			// 1. Check cache
			// 2. Check URL
			// 3. Nothing

			// Create a promise
			var deffered = $q.defer();
			var SchoolService = this;
			if (this.savedSchool !== null) {
				// Load cached school
				deffered.resolve(this.savedSchool);
			} else if ($routeParams.school !== undefined) {
				// Grab the school slug from the url
				var slug = $routeParams.school;
				this._getSchoolBySlug(slug)
					.then(function(response) {
						SchoolService.setSavedSchool(response.data);
						deffered.resolve(response.data);
					}, function(error, status) {
						deffered.reject('Failed to get school: ' + status);
					});
			} else {
				// No school saved
				deffered.reject('No school saved.');
			}

			return deffered.promise;
		},

		'setSavedSchool': function(school) {
			if (school !== null && school !== undefined) {
				this.savedSchool = school;
				console.log("Setting saved school as " + school.name);
			}
		},

		'deleteSavedSchool': function() {
			this.savedSchool = null;
		},

		'_getSchoolBySlug': function(slug) {
			return $http.get(config.API_URL + '/schools/' + slug);
		},

		'_getSchoolList': function() {
			return $http.get(config.API_URL + '/schools');
		},

		'_setSchoolList': function(schools) {
			this.schools = schools;
		}

	};
	return school;
}]);
