


pipeline {
    agent {
        label 'general'
    }

    triggers {
        githubPush()
    }

    options {
        timeout(time: 20, unit: 'MINUTES')  // discard the build after 20 minutes of running
        timestamps()  // display timestamp in console output
    }

    environment {
        IMAGE_TAG = "0.0.$BUILD_NUMBER"
        DOCKER_CREDS = credentials('dockerhub')
        DOCKER_USERNAME = "${DOCKER_CREDS_USR}"  // The _USR suffix added to access the username value
        DOCKER_PASS = "${DOCKER_CREDS_PSW}"      // The _PSW suffix added to access the password value
        SERVICES_TO_DEPLOY = ""
        ALL_SERVICES = "finance-tracker-frontend,category-service,transaction-service,users-service,reports-service"
    }

    stages {
        stage('buffer')  {
            steps {
                script {
                    sh 'git config --global http.postBuffer 524288000'
                }
            }
        }
        stage('Checkout') {
            steps {
                checkout([$class: 'GitSCM', 
                    branches: [[name: 'main']], 
                    doGenerateSubmoduleConfigurations: false, 
                    extensions: [[$class: 'CloneOption', timeout: 60]], // Timeout in minutes
                    submoduleCfg: [], 
                    userRemoteConfigs: [[url: 'https://github.com/MohammadKhGh99/PersonalFinanceTracker']]
                ])
            }
        }
        stage('Retry') {
            steps {
                retry(3) { // Retries up to 3 times
                    checkout scm
                }
            }
        }
        stage('Docker setup') {
            steps {
                sh '''
                  docker login -u $DOCKER_USERNAME -p $DOCKER_PASS
                '''
            }
        }

        stage('Check for Modifications') {
            steps {
                script {
                    def all_services = ALL_SERVICES.split(',')
                    def modifiedFiles = sh(script: "git diff --name-only $GIT_PREVIOUS_COMMIT $GIT_COMMIT", returnStdout: true).trim().split('\n')
                    def services = []
                    def images = []

                    for (service in all_services) {
                        if (modifiedFiles.any { it.startsWith("${service}/") }) {
                            def image = "${DOCKER_USERNAME}/${service}:${IMAGE_TAG}"
                            
                            services.add(service)
                            images.add(image)

                            sh """
                              cd ${service}
                              docker build -t ${image} .
                              docker push ${image}
                              cd ..
                            """
                        }
                    }

                    withEnv(["SERVICES_TO_DEPLOY=${services.join(',')}", "IMAGES=${images.join(',')}"]) {
                        echo "Services to deploy: ${env.SERVICES_TO_DEPLOY}"
                        echo "Images: ${env.IMAGES}"
                    }
                }
            }
        }

        stage('Trigger Deploy') {
            steps {
                script {
                    if (env.SERVICES_TO_DEPLOY) {
                        build job: 'FinanceTrackerDeploy', wait: false, parameters: [
                            string(name: 'SERVICE_NAMES', value: env.SERVICES_TO_DEPLOY),
                            string(name: 'IMAGE_FULL_NAMES', value: env.IMAGES)
                        ]
                    } else {
                        echo "No services to deploy."
                    }
                }
            }
        }
    }
}