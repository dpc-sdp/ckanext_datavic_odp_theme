'use strict';
module.exports = function(grunt) {

  grunt.initConfig({
    sass: {
      dist: {
        options: {
          style: 'compressed',
          compass: false,
          sourcemap: false
        },
        files: {
          '../webassets/datavic_odp_theme.css': [
            'sass/styles.scss'
          ]
        }
      }
    },
    watch: {
      sass: {
        files: [
          'sass/**/*.scss'
        ],
        tasks: ['sass']
      }
    }
  });

  // Load tasks
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-sass');

  // Register tasks
  grunt.registerTask('default', [
    'sass'
  ]);
  grunt.registerTask('dev', [
    'watch'
  ]);

};