pipeline {
    // The Jenkins Docker container mounts the project here.
    agent {
        node {
            label 'built-in'
            customWorkspace '/var/jenkins_home/project'
        }
    }

    environment {
        BMC_URL = 'https://127.0.0.1:2443'
        BMC_WEB_URL = 'https://127.0.0.1:2443'
        BMC_USER = 'root'
        BMC_PASSWORD = '0penBmc'
        OPENBMC_LAB_DIR = "${HOME}/openbmc-lab"
    }

    stages {
        stage('Prepare Python Environment') {
            steps {
                sh 'python3 -m venv .venv'
                sh '. .venv/bin/activate && pip install --upgrade pip pytest requests selenium locust'
                sh 'mkdir -p reports'
                sh 'python3 --version > reports/environment.txt'
                sh '. .venv/bin/activate && pip list >> reports/environment.txt'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports/environment.txt', allowEmptyArchive: true
                }
            }
        }

        stage('Start OpenBMC in QEMU') {
            steps {
                sh '''
                    test -f "$OPENBMC_LAB_DIR/romulus.static.mtd"
                    cp "$OPENBMC_LAB_DIR/romulus.static.mtd" romulus-ci.static.mtd
                    nohup qemu-system-arm -m 256 -M romulus-bmc -nographic \
                      -drive file=romulus-ci.static.mtd,format=raw,if=mtd \
                      -net nic \
                      -net user,hostfwd=tcp:0.0.0.0:2222-:22,hostfwd=tcp:0.0.0.0:2443-:443,hostfwd=udp:0.0.0.0:2623-:623,hostname=qemu \
                      > qemu.log 2>&1 &
                    echo $! > qemu.pid
                    sleep 90
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'qemu.log', allowEmptyArchive: true
                }
            }
        }

        stage('Run Redfish API Tests') {
            steps {
                sh '. .venv/bin/activate && pytest -q labs_4_8/test_redfish.py --junitxml=reports/redfish-tests.xml'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports/redfish-tests.xml', allowEmptyArchive: true
                }
            }
        }

        stage('Run Web UI Tests') {
            steps {
                sh '. .venv/bin/activate && pytest -q labs_4_8/openbmc_auth_tests.py --junitxml=reports/webui-tests.xml'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports/webui-tests.xml', allowEmptyArchive: true
                }
            }
        }

        stage('Run Load Test') {
            steps {
                sh '''
                    . .venv/bin/activate
                    locust -f labs_4_8/locustfile.py --headless -u 10 -r 2 -t 1m \
                      --csv reports/locust-openbmc || true
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports/locust-openbmc*', allowEmptyArchive: true
                }
            }
        }
    }

    post {
        always {
            sh 'test -f qemu.pid && kill $(cat qemu.pid) || true'
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
        }
    }
}
