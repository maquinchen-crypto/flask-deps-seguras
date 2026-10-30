pipeline {
    agent any

    environment {
        PIPENV_VENV_IN_PROJECT = '1'   // el virtualenv queda en .venv dentro del workspace
        PIPENV_NOSPIN          = '1'   // salida limpia en la consola de Jenkins
        REPORTS                = 'reports'
        APP_PORT               = '8000'  // en macOS el 5000 lo ocupa AirPlay Receiver
    }

    triggers {
        // Re-audita todos los días hábiles aunque nadie haga commit:
        // aparecen CVE nuevos sobre versiones que ayer eran "seguras".
        cron('H 7 * * 1-5')
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '20'))
        disableConcurrentBuilds()
    }

    stages {
        stage('Build') {
            steps {
                sh 'mkdir -p $REPORTS'
                sh 'which python3 pipenv && python3 --version && pipenv --version'
                // --deploy: falla si Pipfile.lock no coincide con Pipfile (nada de versiones "sorpresa")
                sh 'pipenv install --dev --deploy'
                sh 'pipenv run python -m py_compile app.py'
            }
        }

        stage('Test') {
            steps {
                sh 'pipenv run python -m pytest -v --junitxml=$REPORTS/junit.xml'
            }
            post {
                always { junit "${REPORTS}/junit.xml" }
            }
        }

        stage('Analyze') {
            steps {
                // Estilo y errores comunes
                sh 'pipenv run flake8 app.py tests --output-file=$REPORTS/flake8.txt --tee'
                // SAST: el build falla si bandit encuentra hallazgos de severidad ALTA
                sh 'pipenv run bandit -r app.py -f txt -o $REPORTS/bandit.txt --severity-level high'
            }
        }

        stage('Dependency Management') {
            steps {
                // 1) Línea base: requirements.txt original del enunciado (solo informe, no corta el build)
                sh '''
                    pipenv run pip-audit -r requirements.txt --no-deps --disable-pip \
                        -f json -o $REPORTS/audit-requirements-original.json || true
                    pipenv run pip-audit -r requirements.txt --no-deps --disable-pip \
                        > $REPORTS/audit-requirements-original.txt 2>&1 || true
                '''
                // 2) Estado y actualizaciones disponibles
                sh 'pipenv graph > $REPORTS/dependency-graph.txt'
                sh 'pipenv update --outdated --dry-run > $REPORTS/outdated.txt 2>&1 || true'
                // 3) Gate: las dependencias bloqueadas que realmente se despliegan NO pueden tener CVE conocidos
                sh '''
                    pipenv requirements --dev > $REPORTS/requirements-lock.txt
                    pipenv run pip-audit -r $REPORTS/requirements-lock.txt --no-deps --disable-pip \
                        -f json -o $REPORTS/audit-lock.json
                '''
            }
        }

        stage('Deploy (test)') {
            steps {
                sh '''
                    pkill -f "gunicorn.*app:app" || true
                    # JENKINS_NODE_COOKIE evita que Jenkins mate el proceso al terminar el build
                    JENKINS_NODE_COOKIE=dontKillMe nohup pipenv run gunicorn -b 127.0.0.1:$APP_PORT app:app \
                        > $REPORTS/deploy.log 2>&1 &
                    sleep 3
                    curl -fsS http://127.0.0.1:$APP_PORT/health
                    curl -fsS "http://127.0.0.1:$APP_PORT/hello?name=Jenkins" | tee $REPORTS/smoke-test.txt
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: "${REPORTS}/**", allowEmptyArchive: true
        }
        success {
            echo 'OK: pipeline completo, dependencias sin vulnerabilidades conocidas.'
        }
        failure {
            echo "ALERTA: build ${env.BUILD_NUMBER} falló. Revisar ${env.BUILD_URL}artifact/reports/"
            // Descomentar cuando el SMTP esté configurado (Manage Jenkins > System > E-mail Notification):
            // mail to: 'tu_correo@duocuc.cl',
            //      subject: "[ALERTA] ${env.JOB_NAME} #${env.BUILD_NUMBER} falló",
            //      body: "Revisar consola y reportes: ${env.BUILD_URL}"
        }
    }
}
