import { fetchSignedUrl } from '@mirego/scout-api';
import {
  LoaderState,
  MicroAppFileInfo,
  MicroAppFileUpload,
  MicroAppHeader,
  MicroAppNewConversationButton,
  MicroAppStep,
  MicroAppStepsContainer,
  useConversationQuery,
  useScoutAppContext,
} from '@mirego/scout-chat';
import '@mirego/scout-chat/style.css';
import axios from 'axios';
import { useCallback, useEffect, useMemo, useState } from 'react';
import AppLogo from './assets/app.svg?react';
import { STEPS_ORDER } from './constants';
import useScoutTranslation from './hooks/use-scout-translation';
import { useFileHandling } from './hooks/useFileHandling';
import { MyExampleUserData, Step } from './types';
import { getFileExtension } from './utils/file';

const App = () => {
  const { conversation_id, redirectToNewConversation } = useScoutAppContext();

  const { t } = useScoutTranslation();

  const [shouldPollConversation, setShouldPollConversation] = useState(false);
  const [currentStep, setCurrentStep] = useState<Step>('idle');

  const conversationQuery = useConversationQuery({
    conversationId: conversation_id,
    refetchInterval: shouldPollConversation ? 1000 : undefined,
  });
  const userData = (conversationQuery.data?.user_data || null) as MyExampleUserData | null;

  const {
    selectedFile,
    setOutputFileBlob,
    setOriginalFileBlob,
    handleFileUpload,
    handleDownloadInputFile,
    handleDownloadOutputFile,
    resetFiles,
    uploadProgress,
  } = useFileHandling(userData, setCurrentStep, t);

  const step = userData?.step || currentStep;

  const currentStepIndex = useMemo(() => {
    return STEPS_ORDER.findIndex(orderedStep => orderedStep === step);
  }, [step]);

  const completedAllSteps = useMemo(() => {
    return currentStepIndex === STEPS_ORDER.length - 1;
  }, [currentStepIndex]);

  const inputFilename = selectedFile?.name || userData?.input_filename;

  useEffect(() => {
    if (conversation_id && userData?.step) {
      const shouldPoll = userData.step !== 'done' && !userData?.error_logs;
      setShouldPollConversation(shouldPoll);
      setCurrentStep(userData.step);
    }
  }, [conversation_id, userData?.step, userData?.error_logs]);

  useEffect(() => {
    const asyncRun = async () => {
      if (!userData) {
        return;
      }
      if (userData.input_protected_file_path) {
        const inputFileSignedUrl = await fetchSignedUrl(userData.input_protected_file_path);
        const inputFile = await axios.get<Blob>(inputFileSignedUrl.data.url, {
          responseType: 'blob',
        });
        setOriginalFileBlob(inputFile.data);
      }

      if (userData.output_protected_file_path) {
        const outputFileSignedUrl = await fetchSignedUrl(userData.output_protected_file_path);
        const outputFile = await axios.get<Blob>(outputFileSignedUrl.data.url, {
          responseType: 'blob',
        });
        setOutputFileBlob(outputFile.data);
      }
    };
    asyncRun();
  }, [userData, setOriginalFileBlob, setOutputFileBlob, resetFiles]);

  const getStepState = useCallback(
    (orderedStep: Step, index: number): LoaderState => {
      if (step === orderedStep && userData?.error_logs) {
        return 'fail';
      }
      if (index < currentStepIndex || completedAllSteps) {
        return 'completed';
      }
      if (index === currentStepIndex) {
        return 'loading';
      }
      return 'idle';
    },
    [completedAllSteps, currentStepIndex, step, userData?.error_logs]
  );

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        width: '100%',
      }}
    >
      {conversation_id && <MicroAppNewConversationButton onClick={redirectToNewConversation} />}
      <MicroAppHeader AppLogo={AppLogo} title={t('title')} subtitle={t('subtitle')} />
      {step === 'idle' || step === 'uploading' ? (
        <MicroAppFileUpload
          supportedFiles="application/pdf"
          maxSize="10MB"
          onFileUpload={handleFileUpload}
          isLoading={step === 'uploading'}
          loadingText={step === 'uploading' ? `${uploadProgress}%` : undefined}
          overrideDropzoneOptions={{
            multiple: false,
            maxFiles: 1,
            accept: {
              'application/pdf': ['.pdf'],
            },
          }}
        />
      ) : (
        <MicroAppStepsContainer>
          {STEPS_ORDER.map((orderedStep, index) => (
            <MicroAppStep
              key={orderedStep}
              state={getStepState(orderedStep, index)}
              title={t(orderedStep)}
              errorMessage={step === orderedStep ? userData?.error_logs || undefined : undefined}
            >
              {inputFilename && orderedStep === 'preparing' && (
                <div style={{ display: 'flex' }}>
                  <MicroAppFileInfo
                    filename={inputFilename}
                    fileType={t(`${getFileExtension(inputFilename)}_file`)}
                    onDownload={handleDownloadInputFile}
                  />
                </div>
              )}

              {orderedStep === 'done' && userData?.output_filename && (
                <div style={{ display: 'flex' }}>
                  <MicroAppFileInfo
                    filename={userData?.output_filename}
                    onDownload={handleDownloadOutputFile}
                  />
                </div>
              )}
            </MicroAppStep>
          ))}
        </MicroAppStepsContainer>
      )}
    </div>
  );
};

const WrappedApp = () => {
  const { conversation_id } = useScoutAppContext();
  return <App key={conversation_id} />;
};

export default WrappedApp;
