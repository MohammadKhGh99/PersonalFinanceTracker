pipeline {
    agent any

    triggers {
        githubPush()
    }

    options {
        timeout(time: 10, unit: 'MINUTES')  // discard the build after 10 minutes of running
        timestamps()  // display timestamp in console output
    }

    environment {
        IMAGE_TAG = "0.0.$BUILD_NUMBER"
        IMAGE_BASE_NAME = "finance_tracker"

        DOCKER_CREDS = credentials('dockerhub')
        DOCKER_USERNAME = "${DOCKER_CREDS_USR}"  // The _USR suffix added to access the username value
        DOCKER_PASS = "${DOCKER_CREDS_PSW}"      // The _PSW suffix added to access the password value
        IMAGE_FULL_NAME="$DOCKER_USERNAME/$IMAGE_BASE_NAME:$IMAGE_TAG"
    }

    stages { 
        stage('Docker setup') {
            steps {
                sh '''
                  docker login -u $DOCKER_USERNAME -p $DOCKER_PASS
                '''
            }
        }

        stage('Build & Push') {
            steps {
                sh '''
                  docker build -t $IMAGE_FULL_NAME .
                  docker push $IMAGE_FULL_NAME
                '''
                echo "Docker image pushed successfully."
            }
        }

        stage('Trigger Deploy') {
            steps {
                build job: 'FinanceTrackerDeploy', wait: false, parameters: [
                    string(name: 'SERVICE_NAME', value: "FinanceTracker"),
                    string(name: 'IMAGE_FULL_NAME_PARAM', value: "${IMAGE_FULL_NAME}")
                ]
            }
        }
    }
}
