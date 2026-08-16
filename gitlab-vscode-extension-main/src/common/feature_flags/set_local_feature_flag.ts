import * as vscode from 'vscode';
import { updateConfig } from '../utils/extension_configuration';
import { FeatureFlag } from './constants';

const FEATURE_FLAGS_CONFIG_NAMESPACE = 'gitlab.featureFlags';

export const setLocalFeatureFlag = async (flag: FeatureFlag, enabled: boolean): Promise<void> => {
  const config = vscode.workspace.getConfiguration(FEATURE_FLAGS_CONFIG_NAMESPACE);
  await updateConfig(config, flag, enabled);
};
