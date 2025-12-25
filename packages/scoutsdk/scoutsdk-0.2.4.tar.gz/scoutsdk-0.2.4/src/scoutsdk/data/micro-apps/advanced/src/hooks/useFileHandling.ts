import { MyCustomFunctionRequest, MyExampleUserData, Step } from '#/types';
import {
  createConversation,
  executeAssistantCustomFunction,
  getSignedUploadUrl,
  updateConversationUserData,
  uploadFile,
} from '@mirego/scout-api';
import { useScoutAppContext } from '@mirego/scout-chat';
import { useCallback, useState } from 'react';
import { downloadFile } from '../utils/file';
import { ScoutTranslationFunction } from './use-scout-translation';

export const useFileHandling = (
  userData: MyExampleUserData | null,
  setCurrentStep: (step: Step) => void,
  t: ScoutTranslationFunction
) => {
  const { assistant_id, conversation_id, onConversationCreated, redirectToConversation } =
    useScoutAppContext();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [originalFileBlob, setOriginalFileBlob] = useState<Blob | null>(null);
  const [outputFileBlob, setOutputFileBlob] = useState<Blob | null>(null);

  const inputFilename = userData?.input_filename || selectedFile?.name;

  const handleFileUpload = useCallback(
    async (files: File[]) => {
      if (conversation_id) {
        console.log('Conversation ID already exists');
        return;
      }
      const file = files[0];
      if (!file) return;

      setSelectedFile(file);
      setCurrentStep('uploading');

      try {
        const fileExtension = file.name.substring(file.name.lastIndexOf('.') + 1);
        const fileName = `original.${fileExtension}`;

        const initialUserData: MyExampleUserData = {
          step: 'preparing',
          input_filename: file.name,
        };

        const conversationResponse = await createConversation({
          title: `${t('title')} - ${file.name}`,
          payload: [],
          assistant_id,
          user_data: initialUserData,
        });

        onConversationCreated(conversationResponse.data);

        const fileBlob = new Blob([file], { type: file.type });
        setOriginalFileBlob(fileBlob);

        const { data: inputSignedUploadResponse } = await getSignedUploadUrl(
          conversationResponse.data.id,
          {
            file_path: fileName,
          }
        );

        await updateConversationUserData(conversationResponse.data.id, {
          input_protected_file_path: inputSignedUploadResponse.protected_url,
          ...initialUserData,
        });

        await uploadFile(conversationResponse.data.id, fileName, file, progressEvent => {
          const percentCompleted = Math.round(progressEvent.progress! * 100);
          setUploadProgress(percentCompleted);
        });

        await executeAssistantCustomFunction<MyCustomFunctionRequest>(
          assistant_id,
          'custom_function_working_with_micro_app',
          {
            input_protected_file_url: inputSignedUploadResponse.protected_url,
            input_original_filename: file.name,
          },
          conversationResponse.data.id
        );

        redirectToConversation(conversationResponse.data.id);
      } catch (error) {
        console.error('Error:', error);
        alert('Error!');
      } finally {
        setUploadProgress(0);
      }
    },
    [
      assistant_id,
      conversation_id,
      onConversationCreated,
      redirectToConversation,
      setCurrentStep,
      t,
    ]
  );

  const handleDownloadInputFile = useCallback(() => {
    if (!originalFileBlob || !inputFilename) {
      console.error('No original file content');
      return;
    }
    downloadFile(originalFileBlob, inputFilename);
  }, [inputFilename, originalFileBlob]);

  const handleDownloadOutputFile = useCallback(() => {
    if (!outputFileBlob || !userData?.output_filename) {
      console.error('No output file content');
      return;
    }
    downloadFile(outputFileBlob, userData.output_filename);
  }, [outputFileBlob, userData?.output_filename]);

  const resetFiles = useCallback(() => {
    setSelectedFile(null);
    setOriginalFileBlob(null);
    setOutputFileBlob(null);
  }, []);

  return {
    selectedFile,
    setOutputFileBlob,
    setOriginalFileBlob,
    handleFileUpload,
    handleDownloadInputFile,
    handleDownloadOutputFile,
    resetFiles,
    uploadProgress,
  };
};
